import React, { useState } from 'react';

interface EditProfilePictureDialogProps {
  isDarkMode: boolean;
  onCancel: () => void;
  onSave: (newProfilePicture: File | null) => Promise<void>;
}

const EditProfilePictureDialog: React.FC<EditProfilePictureDialogProps> = ({
  isDarkMode,
  onCancel,
  onSave,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async () => {
    setError(null);
    if (selectedFile) {
      try {
        await onSave(selectedFile);
        onCancel();
      } catch (err) {
        setError('Failed to update avatar. Please try again.');
      }
    } else {
      setError('Please select an avatar image.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className={`w-96 rounded p-6 shadow-md ${isDarkMode ? 'bg-slate-800 text-slate-100' : 'bg-white text-slate-900'}`}>
        <h2 className="mb-4 text-xl">Update Avatar</h2>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        {preview ? (
          <img src={preview} alt="Preview" className="mb-4 w-32 h-32 object-cover rounded-full" />
        ) : (
          <p className="mb-4">Choose an image for your avatar.</p>
        )}
        <input type="file" accept="image/*" onChange={handleFileChange} className="mb-4" />
        <div className="flex justify-end">
          <button
            onClick={onCancel}
            className={`mr-2 rounded p-2 ${isDarkMode ? 'bg-slate-600 hover:bg-slate-500' : 'bg-gray-300 hover:bg-gray-400'}`}
          >
            Cancel
          </button>
          <button onClick={handleSubmit} className="p-2 bg-blue-500 text-white rounded">
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditProfilePictureDialog;
