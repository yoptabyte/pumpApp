import React, { useCallback, useContext, useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import QRCode from 'react-qr-code';
import DarkModeToggle from '../components/DarkModeToggle';
import Modal from '../components/Modal';
import { checkTelegramLink, linkTelegram } from '../services/api';
import { AuthContext } from '../contexts/AuthContext';
import { ThemeContext } from '../contexts/ThemeContext';

const AppLayout: React.FC = () => {
  const { user, logout } = useContext(AuthContext);
  const { isDarkMode, toggleDarkMode } = useContext(ThemeContext);
  const navigate = useNavigate();

  const [isLinked, setIsLinked] = useState(false);
  const [isLinkingTelegram, setIsLinkingTelegram] = useState(false);
  const [linkingCode, setLinkingCode] = useState<string | null>(null);
  const [linkingError, setLinkingError] = useState<string | null>(null);

  const fetchTelegramLinkStatus = useCallback(async () => {
    try {
      const response = await checkTelegramLink();
      setIsLinked(response.data.linked);
    } catch {
    }
  }, []);

  useEffect(() => {
    if (!user) {
      setIsLinked(false);
      return;
    }

    fetchTelegramLinkStatus();
  }, [fetchTelegramLinkStatus, user]);

  const handleLinkTelegram = async () => {
    try {
      const response = await linkTelegram();
      setLinkingCode(response.data.code);
      setIsLinkingTelegram(true);
      setLinkingError(null);
    } catch {
      setLinkingError('Failed to generate code. Please try again later.');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `mb-4 ${isDarkMode ? 'text-slate-100' : 'text-gray-800'} ${
      isActive ? 'font-semibold underline' : ''
    }`;

  return (
    <div
      className={`min-h-screen transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-900 text-slate-100' : 'bg-gray-100 text-slate-900'
      }`}
    >
      <DarkModeToggle isDarkMode={isDarkMode} toggleDarkMode={toggleDarkMode} />
      <div className="flex min-h-screen">
        <nav
          className={`fixed left-0 top-0 flex h-full w-64 flex-col p-4 ${
            isDarkMode ? 'bg-slate-800' : 'bg-gray-200'
          }`}
        >
          <NavLink to="/" end className={navLinkClass}>
            Home
          </NavLink>
          <NavLink to="/calendar" className={navLinkClass}>
            Training Calendar
          </NavLink>
          <NavLink to="/all-posts" className={navLinkClass}>
            All Posts
          </NavLink>

          {!isLinked && user && (
            <button
              onClick={handleLinkTelegram}
              className="mb-4 rounded bg-green-500 p-2 text-white hover:bg-green-600"
            >
              Link with Telegram
            </button>
          )}

          {isLinked && <div className="mb-4 rounded bg-blue-500 p-2 text-white">Telegram Linked</div>}

          {user ? (
            <button onClick={handleLogout} className="mt-auto rounded bg-red-500 p-2 text-white hover:bg-red-600">
              Logout
            </button>
          ) : null}
        </nav>

        <main className={`ml-64 flex-1 p-4 ${isDarkMode ? 'bg-slate-900' : 'bg-gray-100'}`}>
          <Outlet />
        </main>
      </div>

      {isLinkingTelegram && linkingCode && (
        <Modal onClose={() => setIsLinkingTelegram(false)}>
          <h2 className="mb-4 text-2xl">Link with Telegram</h2>
          <p>To link your account with Telegram, follow these steps:</p>
          <ol className="mt-2 list-inside list-decimal">
            <li>Scan the QR code below with your phone.</li>
            <li>Open the Telegram bot that appears after scanning.</li>
          </ol>
          <div className="mt-4 flex justify-center">
            <QRCode value={`https://t.me/reminder_training_bot?start=${linkingCode}`} size={256} />
          </div>
          <p className="mt-4">After scanning the QR code, your account will be linked automatically.</p>
          {linkingError && <p className="mt-2 text-red-500">{linkingError}</p>}
          <button
            onClick={() => setIsLinkingTelegram(false)}
            className="mt-4 rounded bg-blue-500 p-2 text-white hover:bg-blue-600"
          >
            Close
          </button>
        </Modal>
      )}
    </div>
  );
};

export default AppLayout;
