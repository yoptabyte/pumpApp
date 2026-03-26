import React from 'react';
import PostItem from './PostItem';
import { Post } from '../types';

interface PostListProps {
  posts: Post[];
  isDarkMode: boolean;
  canEdit: boolean;
  canDelete: boolean;
  startEditing?: (post: Post) => void;
  showDeleteConfirmation?: (id: number) => void;
}

const PostList: React.FC<PostListProps> = ({
  posts,
  isDarkMode,
  canEdit,
  canDelete,
  startEditing,
  showDeleteConfirmation,
}) => {
  return (
    <div>
      {posts.map((post) => (
        <PostItem
          key={post.id}
          post={post}
          isDarkMode={isDarkMode}
          canEdit={canEdit}
          canDelete={canDelete}
          startEditing={startEditing ? () => startEditing(post) : undefined}
          showDeleteConfirmation={
            showDeleteConfirmation ? () => showDeleteConfirmation(post.id) : undefined
          }
        />
      ))}
    </div>
  );
};

export default PostList;
