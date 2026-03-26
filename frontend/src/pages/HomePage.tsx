import React, { useState, useEffect, useCallback, useContext } from 'react';
import { ExtendedPost, ExtendedMediaItem, UserData, AuthUser } from '../types';
import {
  getMyPosts,
  createPost,
  updatePost,
  deletePost,
  getProfile,
  updateProfile,
} from '../services/api';
import SearchBar from '../components/SearchBar';
import PostList from '../components/PostList';
import DeleteDialog from '../components/DeleteDialog';
import EditPostDialog from '../components/EditPostDialog';
import QuickEditPostDialog from '../components/QuickEditPostDialog';
import EditProfilePictureDialog from '../components/EditProfilePictureDialog';
import { AuthContext } from '../contexts/AuthContext';
import { ThemeContext } from '../contexts/ThemeContext';
import config from '../config';
import { withExtendedMedia, withExtendedMediaList } from '../utils/posts';

const BACKEND_ORIGIN =
  config.authBaseUrl === '/'
    ? typeof window !== 'undefined'
      ? window.location.origin
      : 'http://localhost:8000'
    : config.authBaseUrl.replace(/\/$/, '');

const HomePage: React.FC = () => {
  const [posts, setPosts] = useState<ExtendedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isQuickEditing, setIsQuickEditing] = useState(false);
  const [quickEditDescription, setQuickEditDescription] = useState('');
  const [editingPost, setEditingPost] = useState<ExtendedPost | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [postToDelete, setPostToDelete] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [userData, setUserData] = useState<UserData>({
    id: 1,
    username: '',
    email: '',
    profilePicture: '',
  });
  const [isEditingProfilePicture, setIsEditingProfilePicture] = useState(false);

  const { user } = useContext(AuthContext);
  const { isDarkMode } = useContext(ThemeContext);

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await getProfile();
      const avatarPath = response.data.avatar || '';
      const avatarUrl = avatarPath ? `${BACKEND_ORIGIN}${avatarPath}?t=${Date.now()}` : '';

      setUserData({
        id: response.data.id,
        username: response.data.username,
        email: response.data.email ?? '',
        profilePicture: avatarUrl,
      });
    } catch (err) {
      setError('Failed to fetch user profile.');
    }
  }, []);

  const fetchPosts = useCallback(async (query?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const postsData = await getMyPosts({
        ordering: '-created_at',
        search: query || undefined,
      });
      setPosts(withExtendedMediaList(postsData));
    } catch (err) {
      setError('Failed to load your posts. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchUserProfile();
    }
  }, [fetchUserProfile, user]);

  useEffect(() => {
    if (user) {
      fetchPosts(searchTerm);
    }
  }, [fetchPosts, searchTerm, user]);

  const buildPostFormData = (post: ExtendedPost): FormData => {
    const formData = new FormData();
    formData.append('title', post.title);
    formData.append('training_type', post.training_type);
    formData.append('description', post.description);

    const existingImageIds = post.images
      .filter((image) => !image.isNew && image.id !== null)
      .map((image) => image.id!) as number[];

    const existingVideoIds = post.videos
      .filter((video) => !video.isNew && video.id !== null)
      .map((video) => video.id!) as number[];

    existingImageIds.forEach((id) => formData.append('existing_images', id.toString()));
    existingVideoIds.forEach((id) => formData.append('existing_videos', id.toString()));

    post.images.forEach((image) => {
      if (image.file) {
        formData.append('images', image.file);
      } else if (image.image_url) {
        formData.append('image_urls', image.image_url);
      }
    });

    post.videos.forEach((video) => {
      if (video.file) {
        formData.append('videos', video.file);
      } else if (video.video_url) {
        formData.append('video_urls', video.video_url);
      }
    });

    return formData;
  };

  const handleDeletePost = async (id: number) => {
    try {
      await deletePost(id);
      setPosts((currentPosts) => currentPosts.filter((post) => post.id !== id));
      setShowDeleteDialog(false);
      setPostToDelete(null);
    } catch (err) {
      setError('Failed to delete post. Please try again.');
    }
  };

  const handleStartEditing = (post: ExtendedPost) => {
    setEditingPost({ ...post });
    setQuickEditDescription(post.description);
    setIsQuickEditing(true);
  };

  const handleOpenAdvancedEditor = () => {
    setIsQuickEditing(false);
    setIsEditing(true);
  };

  const handleKeepUnchanged = () => {
    setIsQuickEditing(false);
    setEditingPost(null);
    setQuickEditDescription('');
  };

  const handleSaveQuickEdit = async () => {
    if (!editingPost) {
      return;
    }

    const updatedPost: ExtendedPost = {
      ...editingPost,
      description: quickEditDescription,
    };

    try {
      const response = await updatePost(updatedPost.id, buildPostFormData(updatedPost));
      setPosts((currentPosts) =>
        currentPosts.map((post) =>
          post.id === updatedPost.id ? withExtendedMedia(response.data) : post
        )
      );
      setIsQuickEditing(false);
      setEditingPost(null);
      setQuickEditDescription('');
    } catch (err) {
      setError('Failed to save post. Please try again.');
    }
  };

  const handleAddNewPost = () => {
    setIsCreating(true);
    setEditingPost({
      id: 0,
      title: '',
      training_type: '',
      description: '',
      images: [],
      videos: [],
      views: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      profile: {
        id: userData.id,
        user: {
          id: userData.id,
          username: userData.username,
          email: userData.email,
        } satisfies AuthUser,
        avatar: userData.profilePicture || '',
        username: userData.username,
        email: userData.email,
      },
    });
  };

  const handleSavePost = async () => {
    if (!editingPost) {
      return;
    }

    try {
      if (isCreating) {
        const response = await createPost(buildPostFormData(editingPost));
        setPosts((currentPosts) => [...currentPosts, withExtendedMedia(response.data)]);
        setIsCreating(false);
      } else {
        const response = await updatePost(editingPost.id, buildPostFormData(editingPost));
        setPosts((currentPosts) =>
          currentPosts.map((post) =>
            post.id === editingPost.id ? withExtendedMedia(response.data) : post
          )
        );
        setIsEditing(false);
      }
      setEditingPost(null);
    } catch (err) {
      setError('Failed to save post. Please try again.');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (editingPost) {
      setEditingPost({
        ...editingPost,
        [e.target.name]: e.target.value,
      });
    }
  };

  const handleTrainingTypeChange = (value: string) => {
    if (!editingPost) {
      return;
    }

    setEditingPost({
      ...editingPost,
      training_type: value,
    });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && editingPost) {
      const files = Array.from(e.target.files);
      const imageFiles = files.filter((file) => file.type.startsWith('image/'));
      const videoFiles = files.filter((file) => file.type.startsWith('video/'));

      setEditingPost({
        ...editingPost,
        images: [
          ...editingPost.images,
          ...imageFiles.map((file) => ({
            id: null,
            file,
            isNew: true,
          })),
        ],
        videos: [
          ...editingPost.videos,
          ...videoFiles.map((file) => ({
            id: null,
            file,
            isNew: true,
          })),
        ],
      });
    }
  };

  const handleRemoveMedia = (type: 'image' | 'video', mediaItem: ExtendedMediaItem) => {
    if (editingPost) {
      if (type === 'image') {
        setEditingPost({
          ...editingPost,
          images: editingPost.images.filter((image) => image !== mediaItem),
        });
      } else {
        setEditingPost({
          ...editingPost,
          videos: editingPost.videos.filter((video) => video !== mediaItem),
        });
      }
    }
  };

  const handleAddMediaUrl = (type: 'image' | 'video', url: string) => {
    if (editingPost) {
      if (type === 'image') {
        setEditingPost({
          ...editingPost,
          images: [
            ...editingPost.images,
            {
              id: null,
              image_url: url,
              isNew: true,
            },
          ],
        });
      } else {
        setEditingPost({
          ...editingPost,
          videos: [
            ...editingPost.videos,
            {
              id: null,
              video_url: url,
              isNew: true,
            },
          ],
        });
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0 && editingPost) {
      const files = Array.from(e.dataTransfer.files);
      const imageFiles = files.filter((file) => file.type.startsWith('image/'));
      const videoFiles = files.filter((file) => file.type.startsWith('video/'));

      setEditingPost({
        ...editingPost,
        images: [
          ...editingPost.images,
          ...imageFiles.map((file) => ({
            id: null,
            file,
            isNew: true,
          })),
        ],
        videos: [
          ...editingPost.videos,
          ...videoFiles.map((file) => ({
            id: null,
            file,
            isNew: true,
          })),
        ],
      });
    }
  };

  const handleSaveProfilePicture = async (newProfilePicture: File | null) => {
    const formData = new FormData();
    if (newProfilePicture) {
      formData.append('avatar', newProfilePicture);
    } else {
      formData.append('avatar', '');
    }

    try {
      await updateProfile(formData);
      await fetchUserProfile();
      setIsEditingProfilePicture(false);
    } catch (err) {
      setError('Failed to update avatar. Please try again.');
    }
  };

  const addPostButtonClass = isDarkMode
    ? 'w-8 h-8 rounded-full bg-slate-600 text-slate-200 hover:bg-slate-500'
    : 'w-8 h-8 rounded-full bg-gray-300 text-gray-700 hover:bg-gray-400';

  return (
    <div className={`${isDarkMode ? 'bg-slate-900 text-slate-100' : 'bg-gray-100 text-gray-900'}`}>
      {user ? (
        <>
          <div className="w-full max-w-4xl p-10">
            <div className="relative mb-6 mt-6 flex items-center">
              {userData.profilePicture ? (
                <img
                  src={userData.profilePicture}
                  alt="User avatar"
                  className="mr-8 h-36 w-36 cursor-pointer rounded-full object-cover"
                  onClick={() => setIsEditingProfilePicture(true)}
                  onError={(e) => {
                    e.currentTarget.src = '/path/to/default/avatar.png';
                  }}
                />
              ) : (
                <div
                  className={`mr-8 flex h-36 w-36 cursor-pointer items-center justify-center rounded-full ${
                    isDarkMode ? 'bg-slate-700' : 'bg-gray-300'
                  }`}
                  onClick={() => setIsEditingProfilePicture(true)}
                >
                  <span className={isDarkMode ? 'text-slate-100' : 'text-gray-700'}>Avatar</span>
                </div>
              )}
              <h2 className={`text-3xl font-bold ${isDarkMode ? 'text-slate-100' : 'text-gray-800'}`}>
                {userData.username}
              </h2>
              <button
                className={`absolute right-2 top-2 flex items-center justify-center text-xl transition-colors duration-300 ${addPostButtonClass}`}
                aria-label="Add new post"
                onClick={handleAddNewPost}
              >
                +
              </button>
            </div>

            <div className="mb-4">
              <SearchBar
                searchTerm={searchTerm}
                setSearchTerm={setSearchTerm}
                isDarkMode={isDarkMode}
              />
            </div>

            {isLoading ? (
              <p>Loading your posts...</p>
            ) : error ? (
              <p className="text-red-500">{error}</p>
            ) : (
              <PostList
                posts={posts}
                isDarkMode={isDarkMode}
                startEditing={handleStartEditing}
                showDeleteConfirmation={(id: number) => {
                  setShowDeleteDialog(true);
                  setPostToDelete(id);
                }}
                canEdit={true}
                canDelete={true}
              />
            )}
          </div>

          {showDeleteDialog && (
            <DeleteDialog
              isDarkMode={isDarkMode}
              onCancel={() => setShowDeleteDialog(false)}
              onConfirm={() => postToDelete !== null && handleDeletePost(postToDelete)}
            />
          )}

          {isQuickEditing && editingPost && (
            <QuickEditPostDialog
              isDarkMode={isDarkMode}
              value={quickEditDescription}
              onChange={setQuickEditDescription}
              onKeepUnchanged={handleKeepUnchanged}
              onSave={handleSaveQuickEdit}
              onOpenAdvancedEditor={handleOpenAdvancedEditor}
            />
          )}

          {(isEditing || isCreating) && editingPost && (
            <EditPostDialog
              isDarkMode={isDarkMode}
              isCreating={isCreating}
              editingPost={editingPost}
              onInputChange={handleInputChange}
              onTrainingTypeChange={handleTrainingTypeChange}
              onFileInputChange={handleFileInputChange}
              onRemoveMedia={handleRemoveMedia}
              onAddMediaUrl={handleAddMediaUrl}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onCancel={() => {
                setIsEditing(false);
                setIsCreating(false);
                setEditingPost(null);
              }}
              onSave={handleSavePost}
            />
          )}

          {isEditingProfilePicture && (
            <EditProfilePictureDialog
              isDarkMode={isDarkMode}
              onCancel={() => setIsEditingProfilePicture(false)}
              onSave={handleSaveProfilePicture}
            />
          )}
        </>
      ) : (
        <p className="p-10">Loading profile...</p>
      )}
    </div>
  );
};

export default HomePage;
