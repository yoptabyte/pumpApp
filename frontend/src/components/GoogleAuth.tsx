import React from 'react';
import { CredentialResponse, GoogleLogin } from '@react-oauth/google';

import config from '../config';
import { ensureCsrfCookie, googleLogin } from '../services/api';

const GoogleAuth: React.FC = () => {
  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    if (credentialResponse.credential == null) {
      return;
    }

    try {
      await ensureCsrfCookie();
      await googleLogin(credentialResponse.credential);
    } catch {
      // Intentionally ignored in this standalone widget.
    }
  };

  if (config.googleClientId == null) {
    return null;
  }

  return <GoogleLogin onSuccess={handleSuccess} onError={() => undefined} />;
};

export default GoogleAuth;
