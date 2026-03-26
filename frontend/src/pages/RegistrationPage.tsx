import React, { useContext, useState } from 'react';
import { AxiosError } from 'axios';
import { Link, useNavigate } from 'react-router-dom';

import { AuthContext } from '../contexts/AuthContext';
import { ApiErrorResponse } from '../types';
import { ensureCsrfCookie, getProfile, register } from '../services/api';
import type { RegisterRequest } from '../services/api';

const RegistrationPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const [formData, setFormData] = useState<RegisterRequest>({
    username: '',
    email: '',
    password: '',
    password2: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.password2) {
      setError('Passwords do not match.');
      return;
    }

    try {
      await ensureCsrfCookie();
      await register(formData);
      const profileResponse = await getProfile();
      login(profileResponse.data.user);
      navigate('/');
    } catch (err) {
      const errorResponse = err as AxiosError<ApiErrorResponse>;
      setError(errorResponse.response?.data?.detail || 'Registration failed.');
    }
  };

  return (
    <div className="registration-page">
      <h2>Create Account</h2>
      {error && <p className="error text-red-500">{error}</p>}
      <form onSubmit={handleSubmit} className="flex flex-col max-w-md mx-auto">
        <input type="text" name="username" placeholder="Username" value={formData.username} onChange={handleChange} required className="mb-2 p-2 border rounded" />
        <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} required className="mb-2 p-2 border rounded" />
        <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required className="mb-2 p-2 border rounded" />
        <input type="password" name="password2" placeholder="Confirm Password" value={formData.password2} onChange={handleChange} required className="mb-4 p-2 border rounded" />
        <button type="submit" className="p-2 bg-blue-500 text-white rounded">Sign Up</button>
      </form>
      <p className="mt-4 text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-500 hover:text-blue-600">
          Sign in
        </Link>
      </p>
    </div>
  );
};

export default RegistrationPage;
