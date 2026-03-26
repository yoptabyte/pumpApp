const normalizeBaseUrl = (value: string): string => {
  const trimmed = value.trim().replace(/\/+$/, '');
  return `${trimmed}/`;
};

const inferApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && window.location?.origin) {
    const { hostname, port, origin } = window.location;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/api/v1/';
    }

    if (port === '3000' || port === '3001') {
      return 'http://localhost:8000/api/v1/';
    }

    return `${origin}/api/v1/`;
  }
  return '/api/v1/';
};

const rawApiBaseUrl =
  import.meta.env.VITE_API_URL ??
  (typeof process !== 'undefined' ? process.env.REACT_APP_API_URL : undefined) ??
  inferApiBaseUrl();
const apiBaseUrl = normalizeBaseUrl(rawApiBaseUrl);
const authBaseUrl = normalizeBaseUrl(
  rawApiBaseUrl.replace(/\/api(?:\/v\d+)?\/?$/, '') || '/'
);
const googleClientId =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ??
  (typeof process !== 'undefined' ? process.env.REACT_APP_GOOGLE_CLIENT_ID : undefined) ??
  null;

const config = {
  apiBaseUrl,
  authBaseUrl,
  googleClientId,
};

export type AppConfig = typeof config;
export default config;
