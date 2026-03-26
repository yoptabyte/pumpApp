import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import config from '../config';
import { AuthUser, Post, Profile, TrainingSession } from '../types';

export const API_URL = config.apiBaseUrl;

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

const authApi = axios.create({
  baseURL: config.authBaseUrl,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

let refreshRequest: Promise<void> | null = null;

const refreshSession = async (): Promise<void> => {
  if (!refreshRequest) {
    refreshRequest = api.post('/auth/session/refresh/').then(() => undefined).finally(() => {
      refreshRequest = null;
    });
  }
  return refreshRequest;
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (!originalRequest || error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (originalRequest.url?.includes('/auth/session/refresh/')) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      await refreshSession();
      return api.request(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  }
);

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  password2: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface GoogleLoginResponse {
  user: AuthUser;
}

export interface ProfileResponse extends Profile {
  user: AuthUser;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type QueryParams = Record<string, string | number | boolean | undefined>;

const unwrapCollection = <T>(payload: T[] | PaginatedResponse<T>): T[] =>
  Array.isArray(payload) ? payload : payload.results;

export const ensureCsrfCookie = () => api.get('/csrf/');
export const getProfile = () => api.get<ProfileResponse>('/me/');
export const updateProfile = (data: FormData) => api.put('/me/', data);
export const logoutSession = () => api.post('/auth/session/logout/');

export const getMyPosts = async (params?: QueryParams): Promise<Post[]> => {
  const response = await api.get<Post[] | PaginatedResponse<Post>>('/posts/', {
    params: { scope: 'mine', ...params },
  });
  return unwrapCollection(response.data);
};

export const getAllPosts = async (params?: QueryParams): Promise<Post[]> => {
  const response = await api.get<Post[] | PaginatedResponse<Post>>('/posts/', {
    params: { scope: 'all', ...params },
  });
  return unwrapCollection(response.data);
};

export const createPost = (data: FormData) => api.post('/posts/', data);
export const updatePost = (id: number, data: FormData) => api.patch(`/posts/${id}/`, data);
export const deletePost = (id: number) => api.delete(`/posts/${id}/`);

export const register = (data: RegisterRequest) =>
  api.post<{ user: AuthUser }>('/register/', data);

export const login = (data: LoginRequest) =>
  api.post<{ user: AuthUser }>('/login/', data);

export const googleLogin = (idToken: string) =>
  authApi.post<GoogleLoginResponse>('/auth/google/login/', { id_token: idToken });

export const getTrainingSessions = async (
  params?: QueryParams
): Promise<TrainingSession[]> => {
  const response = await api.get<TrainingSession[] | PaginatedResponse<TrainingSession>>('/training-sessions/', {
    params,
  });
  return unwrapCollection(response.data);
};

export const createTrainingSession = (
  data: Partial<TrainingSession>
): Promise<AxiosResponse<TrainingSession>> => api.post('/training-sessions/', data);

export const updateTrainingSession = (
  id: number,
  data: Partial<TrainingSession>
): Promise<AxiosResponse<TrainingSession>> => api.patch(`/training-sessions/${id}/`, data);

export const deleteTrainingSession = (id: number): Promise<AxiosResponse<void>> =>
  api.delete(`/training-sessions/${id}/`);

export const linkTelegram = () => api.post('/me/telegram-link/');
export const checkTelegramLink = () => api.get('/me/telegram-link/');
export const confirmLinkTelegram = (code: string, telegramUserId: string) =>
  api.post('/bot/telegram-link/confirm/', { code, telegram_user_id: telegramUserId });
