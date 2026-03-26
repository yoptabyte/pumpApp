import React, { useState, useEffect, useCallback, useContext } from 'react';
import { ExtendedPost } from '../types';
import { getAllPosts } from '../services/api';
import PostList from '../components/PostList';
import { AuthContext } from '../contexts/AuthContext';
import { ThemeContext } from '../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { withExtendedMediaList } from '../utils/posts';

const AllPostsPage: React.FC = () => {
  const [posts, setPosts] = useState<ExtendedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { user } = useContext(AuthContext);
  const { isDarkMode } = useContext(ThemeContext);
  const navigate = useNavigate();

  const fetchAllPosts = useCallback(async (query?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const postsData = await getAllPosts({
        ordering: '-created_at',
        search: query || undefined,
      });
      setPosts(withExtendedMediaList(postsData));
    } catch (err) {
      setError('Failed to load posts. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchAllPosts(searchTerm);
    } else {
      navigate('/login');
    }
  }, [fetchAllPosts, navigate, searchTerm, user]);

  return (
    <div className={`${isDarkMode ? 'bg-slate-900 text-slate-100' : 'bg-gray-100 text-slate-900'}`}>
      {user ? (
        <div className="max-w-4xl w-full p-10">
          <h2 className="text-3xl font-bold mb-6">All Users' Posts</h2>
          <div className="mb-4">
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by username, title, or post content"
              className={`w-full rounded-lg border px-4 py-2 outline-none transition-colors ${
                isDarkMode
                  ? 'border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-400 focus:border-blue-500'
                  : 'border-slate-300 bg-white text-slate-900 placeholder-slate-500 focus:border-blue-500'
              }`}
            />
          </div>
          {isLoading ? (
            <p>Loading posts...</p>
          ) : error ? (
            <p className="text-red-500">{error}</p>
          ) : (
            <PostList
              posts={posts}
              isDarkMode={isDarkMode}
              canEdit={false}
              canDelete={false}
            />
          )}
        </div>
      ) : null}
    </div>
  );
};

export default AllPostsPage;
