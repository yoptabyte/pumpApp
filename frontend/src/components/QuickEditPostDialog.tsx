import React from 'react';

interface QuickEditPostDialogProps {
  isDarkMode: boolean;
  value: string;
  onChange: (value: string) => void;
  onKeepUnchanged: () => void;
  onSave: () => void;
  onOpenAdvancedEditor: () => void;
}

const QuickEditPostDialog: React.FC<QuickEditPostDialogProps> = ({
  isDarkMode,
  value,
  onChange,
  onKeepUnchanged,
  onSave,
  onOpenAdvancedEditor,
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div
        className={`w-full max-w-lg rounded-xl p-6 shadow-xl ${
          isDarkMode ? 'bg-slate-800 text-slate-100' : 'bg-white text-slate-900'
        }`}
      >
        <h2 className="mb-3 text-xl font-semibold">Edit post content</h2>
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className={`mb-5 min-h-32 w-full rounded-lg border p-3 outline-none focus:ring-2 ${
            isDarkMode
              ? 'border-slate-600 bg-slate-700 text-slate-100 focus:ring-blue-500'
              : 'border-slate-300 bg-white text-slate-900 focus:ring-blue-400'
          }`}
          placeholder="Update the post description"
        />
        <div className="flex flex-wrap justify-end gap-2">
          <button
            onClick={onOpenAdvancedEditor}
            className={`rounded px-4 py-2 ${
              isDarkMode
                ? 'bg-slate-600 text-slate-100 hover:bg-slate-500'
                : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
            }`}
          >
            Advanced edit
          </button>
          <button
            onClick={onKeepUnchanged}
            className={`rounded px-4 py-2 ${
              isDarkMode
                ? 'bg-slate-700 text-slate-100 hover:bg-slate-600'
                : 'bg-gray-100 text-slate-900 hover:bg-gray-200'
            }`}
          >
            Keep unchanged
          </button>
          <button
            onClick={onSave}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Save changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickEditPostDialog;
