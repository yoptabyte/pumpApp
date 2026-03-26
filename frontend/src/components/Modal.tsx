import React from 'react';

interface ModalProps {
  onClose: () => void;
  children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ onClose, children }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="relative w-full max-w-md rounded-lg bg-white p-6 text-slate-900 dark:bg-slate-800 dark:text-slate-100">
        <button
          onClick={onClose}
          className="absolute right-2 top-2 text-gray-500 hover:text-gray-700 dark:text-slate-300 dark:hover:text-white"
        >
          &#10005;
        </button>
        {children}
      </div>
    </div>
  );
};

export default Modal;
