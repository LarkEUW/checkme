import client, { setAuthToken } from './client.js';

export const login = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const { data } = await client.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });

  setAuthToken(data.access_token);
  return data;
};

export const register = async ({ email, password, fullName }) => {
  const { data } = await client.post('/auth/register', {
    email,
    password,
    full_name: fullName
  });
  return data;
};

export const getProfile = async (token) => {
  if (token) {
    setAuthToken(token);
  }
  const { data } = await client.get('/auth/me');
  return data;
};

export const logout = async () => {
  await client.post('/auth/logout');
  setAuthToken(null);
};
