import React from 'react';

interface DeleteDialogProps {
  isDarkMode: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

const DeleteDialog: React.FC<DeleteDialogProps> = ({ isDarkMode, onCancel, onConfirm }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className={`rounded-lg p-6 ${isDarkMode ? 'bg-slate-800 text-slate-100' : 'bg-white text-slate-900'}`}>
        <h2 className="mb-4 text-xl font-bold">Delete Post</h2>
        <p className="mb-4">This post will be permanently deleted. Continue?</p>
        <div className="flex justify-end">
          <button
            className={`mr-2 rounded px-4 py-2 ${isDarkMode ? 'bg-slate-600 hover:bg-slate-500' : 'bg-gray-300 hover:bg-gray-400'}`}
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600"
            onClick={onConfirm}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteDialog;
