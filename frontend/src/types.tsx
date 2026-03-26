export interface UserData {
  id: number;
  username: string;
  email: string;
  profilePicture: string;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
}

export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

export interface Profile {
  id: number;
  user: AuthUser;
  username: string;
  email?: string;
  avatar: string | null;
}


export interface MediaItem {
  id: number | null;
  image?: string;
  video?: string;
  image_url?: string;
  video_url?: string;
}

export interface ExtendedMediaItem extends MediaItem {
  file?: File;
  isNew?: boolean;
}


export interface Post {
  id: number;
  title: string;
  training_type: string;
  description: string;
  images: MediaItem[];
  videos: MediaItem[];
  views: number;
  created_at: string;
  updated_at: string;
  profile: Profile;
}

export interface ExtendedPost extends Omit<Post, 'images' | 'videos'> {
  images: ExtendedMediaItem[];
  videos: ExtendedMediaItem[];
}


export interface TrainingSession {
  id: number;
  date: string;
  time: string;
  recurrence: string;
  days_of_week?: string;
}


export interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
}
