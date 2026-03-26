import React from 'react';

interface SearchBarProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  isDarkMode: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ searchTerm, setSearchTerm, isDarkMode }) => {
  return (
    <div className="relative w-full max-w-md">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg
          className={`w-5 h-5 ${
            isDarkMode ? 'text-gray-400' : 'text-gray-500'
          }`}
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
      </div>
      <input
        type="text"
        placeholder="Search by post, training type, or username"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className={`w-full py-2 pl-10 pr-4 rounded-full ${
          isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-900'
        } focus:outline-none focus:ring-2 focus:ring-indigo-500`}
      />
    </div>
  );
};

export default SearchBar;
