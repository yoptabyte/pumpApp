import React, { useContext, useState } from 'react';
import { CredentialResponse, GoogleLogin } from '@react-oauth/google';
import { AxiosError } from 'axios';
import { Link, useNavigate } from 'react-router-dom';

import config from '../config';
import { AuthContext } from '../contexts/AuthContext';
import { ApiErrorResponse } from '../types';
import { ensureCsrfCookie, getProfile, googleLogin, login as loginRequest } from '../services/api';
import type { LoginRequest } from '../services/api';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login: loginContext } = useContext(AuthContext);

  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);

  const finalizeLogin = async () => {
    const userResponse = await getProfile();
    loginContext(userResponse.data.user);
    navigate('/');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await ensureCsrfCookie();
      await loginRequest(formData);
      await finalizeLogin();
    } catch (err) {
      const errorResponse = err as AxiosError<ApiErrorResponse>;
      setError(errorResponse.response?.data?.detail || errorResponse.response?.data?.message || 'Login failed.');
    }
  };

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      setError('Failed to retrieve Google credentials.');
      return;
    }

    try {
      await ensureCsrfCookie();
      await googleLogin(credentialResponse.credential);
      await finalizeLogin();
    } catch (err) {
      const errorResponse = err as AxiosError<ApiErrorResponse>;
      setError(errorResponse.response?.data?.detail || errorResponse.response?.data?.message || 'An error occurred during Google authentication.');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="login-page">
      <h2>Sign In</h2>
      {error && <p className="error text-red-500">{error}</p>}
      <form onSubmit={handleSubmit} className="flex flex-col max-w-md mx-auto">
        <input
          type="text"
          name="username"
          placeholder="Username or Email"
          value={formData.username}
          onChange={handleChange}
          required
          className="mb-2 p-2 border rounded"
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
          className="mb-4 p-2 border rounded"
        />
        <button type="submit" className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600">
          Sign In
        </button>
      </form>
      <div className="google-login flex justify-center mt-4">
        {config.googleClientId ? (
          <GoogleLogin onSuccess={handleGoogleSuccess} onError={() => setError('Google sign-in failed.')} />
        ) : (
          <p className="text-sm text-gray-500">Google login is not configured.</p>
        )}
      </div>
      <p className="mt-4 text-center text-sm text-gray-500">
        Don't have an account?{' '}
        <Link to="/register" className="text-blue-500 hover:text-blue-600">
          Sign up
        </Link>
      </p>
    </div>
  );
};

export default LoginPage;
