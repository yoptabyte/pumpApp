import { ExtendedMediaItem, ExtendedPost, Post } from '../types';

export const withExtendedMedia = (post: Post): ExtendedPost => ({
  ...post,
  images: post.images.map((image) => ({ ...image, file: undefined } as ExtendedMediaItem)),
  videos: post.videos.map((video) => ({ ...video, file: undefined } as ExtendedMediaItem)),
});

export const withExtendedMediaList = (posts: Post[]): ExtendedPost[] =>
  posts.map(withExtendedMedia);
