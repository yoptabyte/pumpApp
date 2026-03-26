import React, { useState } from 'react';
import { ExtendedPost, ExtendedMediaItem } from '../types';

interface EditPostDialogProps {
  isDarkMode: boolean;
  isCreating: boolean;
  editingPost: ExtendedPost;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onTrainingTypeChange: (value: string) => void;
  onFileInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveMedia: (type: 'image' | 'video', mediaItem: ExtendedMediaItem) => void;
  onAddMediaUrl: (type: 'image' | 'video', url: string) => void;
  onDragOver: (e: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  onCancel: () => void;
  onSave: () => void;
}

const workoutOptions = [
  'Arm Day',
  'Leg Day',
  'Back Day',
  'Chest Day',
  'Full Body',
  'Cardio',
  'Abs',
];

const parseTrainingTypes = (value: string): string[] =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const EditPostDialog: React.FC<EditPostDialogProps> = ({
  isDarkMode,
  isCreating,
  editingPost,
  onInputChange,
  onTrainingTypeChange,
  onFileInputChange,
  onRemoveMedia,
  onAddMediaUrl,
  onDragOver,
  onDrop,
  onCancel,
  onSave,
}) => {
  const [imageUrl, setImageUrl] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const selectedTrainingTypes = parseTrainingTypes(editingPost.training_type);

  const handleAddImageUrl = () => {
    if (imageUrl) {
      onAddMediaUrl('image', imageUrl);
      setImageUrl('');
    }
  };

  const handleAddVideoUrl = () => {
    if (videoUrl) {
      onAddMediaUrl('video', videoUrl);
      setVideoUrl('');
    }
  };

  const toggleChip = (item: string) => {
    const current = parseTrainingTypes(editingPost.training_type);
    const next = current.includes(item)
      ? current.filter((i) => i !== item)
      : [...current, item];
    onTrainingTypeChange(next.join(', '));
  };

  const removeChip = (e: React.MouseEvent<HTMLSpanElement>, item: string) => {
    e.stopPropagation();
    const next = parseTrainingTypes(editingPost.training_type).filter((i) => i !== item);
    onTrainingTypeChange(next.join(', '));
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
    >
      <div
        className={`w-full max-w-2xl rounded-lg border p-8 shadow-2xl ${
          isDarkMode
            ? 'border-slate-700 bg-slate-800 text-slate-100'
            : 'border-slate-200 bg-white text-slate-900'
        } max-h-[90vh] overflow-y-auto`}
      >
        <h2 className="text-2xl font-bold mb-4">{isCreating ? 'Create New Post' : 'Edit Post'}</h2>
        <input
          type="text"
          name="title"
          value={editingPost.title}
          onChange={onInputChange}
          placeholder="Title"
          className={`mb-4 w-full rounded p-2 ${
            isDarkMode ? 'bg-slate-700 text-slate-100 placeholder-slate-400' : 'bg-gray-100'
          }`}
        />
        <input
          type="text"
          name="training_type"
          value={editingPost.training_type}
          onChange={(event) => onTrainingTypeChange(event.target.value)}
          placeholder="Training Type (comma separated)"
          className={`mb-3 w-full rounded p-2 ${
            isDarkMode ? 'bg-slate-700 text-slate-100 placeholder-slate-400' : 'bg-gray-100'
          }`}
        />
        <div className="mb-4 flex flex-wrap gap-2">
          {workoutOptions.map((item) => {
            const isSelected = selectedTrainingTypes.includes(item);

            return (
              <button
                key={item}
                type="button"
                onClick={() => toggleChip(item)}
                className={`inline-flex items-center rounded-full border px-3 py-1 text-sm transition-colors ${
                  isSelected
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : isDarkMode
                      ? 'border-slate-500 bg-slate-700 text-slate-100 hover:bg-slate-600'
                      : 'border-slate-300 bg-white text-slate-900 hover:bg-slate-100'
                }`}
              >
                <span>{item}</span>
                {isSelected && (
                  <span onClick={(e) => removeChip(e, item)} className="ml-2 text-xs leading-none">
                    ✕
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <textarea
          name="description"
          value={editingPost.description}
          onChange={onInputChange}
          placeholder="Description"
          className={`mb-4 w-full rounded p-2 ${
            isDarkMode ? 'bg-slate-700 text-slate-100 placeholder-slate-400' : 'bg-gray-100'
          }`}
          rows={4}
        />

        <div className="mb-4">
          <input
            type="text"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="Image URL"
            className={`mb-2 w-full rounded p-2 ${
              isDarkMode ? 'bg-slate-700 text-slate-100 placeholder-slate-400' : 'bg-gray-100'
            }`}
          />
          <button
            onClick={handleAddImageUrl}
            className={`px-4 py-2 rounded ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
          >
            Add Image from URL
          </button>
        </div>

        <div className="mb-4">
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="Video URL"
            className={`mb-2 w-full rounded p-2 ${
              isDarkMode ? 'bg-slate-700 text-slate-100 placeholder-slate-400' : 'bg-gray-100'
            }`}
          />
          <button
            onClick={handleAddVideoUrl}
            className={`px-4 py-2 rounded ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
          >
            Add Video from URL
          </button>
        </div>

        {editingPost.images.length > 0 && (
          <div className="mb-4">
            <p className="font-bold mb-2">Images:</p>
            <div className="grid grid-cols-4 gap-4">
              {editingPost.images.map((image, index) => {
                const imageKey =
                  image.id ??
                  image.image_url ??
                  image.image ??
                  (image.file ? `${image.file.name}-${index}` : `image-${index}`);

                return (
                  <div key={imageKey} className="relative">
                    {image.file ? (
                      <img
                        src={URL.createObjectURL(image.file)}
                        alt="Image"
                        className="w-full h-20 object-cover rounded"
                      />
                    ) : image.image_url ? (
                      <img src={image.image_url} alt="Image" className="w-full h-20 object-cover rounded" />
                    ) : image.image ? (
                      <img src={image.image} alt="Image" className="w-full h-20 object-cover rounded" />
                    ) : null}
                    <button onClick={() => onRemoveMedia('image', image)} className="absolute top-1 right-1 text-red-500">
                      🗑️
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {editingPost.videos.length > 0 && (
          <div className="mb-4">
            <p className="font-bold mb-2">Videos:</p>
            <div className="grid grid-cols-4 gap-4">
              {editingPost.videos.map((video, index) => {
                const videoKey =
                  video.id ??
                  video.video_url ??
                  video.video ??
                  (video.file ? `${video.file.name}-${index}` : `video-${index}`);

                return (
                  <div key={videoKey} className="relative">
                    {video.file ? (
                      <video src={URL.createObjectURL(video.file)} className="w-full h-20 object-cover rounded" controls />
                    ) : video.video_url ? (
                      video.video_url.includes('youtube.com') || video.video_url.includes('youtu.be') ? (
                        <iframe
                          src={`https://www.youtube.com/embed/${extractYouTubeID(video.video_url)}`}
                          title="YouTube video"
                          className="w-full h-20 object-cover rounded"
                          allowFullScreen
                        ></iframe>
                      ) : (
                        <video src={video.video_url} className="w-full h-20 object-cover rounded" controls />
                      )
                    ) : video.video ? (
                      <video src={video.video} className="w-full h-20 object-cover rounded" controls />
                    ) : null}
                    <button onClick={() => onRemoveMedia('video', video)} className="absolute top-1 right-1 text-red-500">
                      🗑️
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div
          onDragOver={onDragOver}
          onDrop={onDrop}
          className={`border-2 border-dashed p-4 mb-4 text-center ${isDarkMode ? 'border-gray-600' : 'border-gray-300'}`}
        >
          <p>Drag files here or</p>
          <input
            type="file"
            onChange={onFileInputChange}
            multiple
            accept="image/*,video/*"
            className="mt-2"
          />
        </div>
        <div className="flex justify-end">
          <button
            onClick={onCancel}
            className={`px-4 py-2 rounded mr-2 ${isDarkMode ? 'bg-gray-600 hover:bg-gray-700' : 'bg-gray-200 hover:bg-gray-300'}`}
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            className={`px-4 py-2 rounded ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
          >
            {isCreating ? 'Create' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

function extractYouTubeID(url: string): string | null {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return match && match[2].length === 11 ? match[2] : null;
}

export default EditPostDialog;
