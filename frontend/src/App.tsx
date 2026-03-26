import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import AppRoutes from './routes/AppRoutes';
import config from './config';

const App: React.FC = () => {
  const appShell = (
    <AuthProvider>
      <ThemeProvider>
        <Router>
          <AppRoutes />
        </Router>
      </ThemeProvider>
    </AuthProvider>
  );

  if (!config.googleClientId) {
    return appShell;
  }

  return (
    <GoogleOAuthProvider clientId={config.googleClientId}>
      {appShell}
    </GoogleOAuthProvider>
  );
};

export default App;
