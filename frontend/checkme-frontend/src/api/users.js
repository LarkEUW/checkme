import client from './client.js';

export const listUsers = async (params = {}) => {
  const { data } = await client.get('/users/', { params });
  return data;
};

export const getUser = async (userId) => {
  const { data } = await client.get(`/users/${userId}`);
  return data;
};

export const updateUser = async (userId, payload) => {
  const { data } = await client.put(`/users/${userId}`, payload);
  return data;
};

export const deleteUser = async (userId) => {
  await client.delete(`/users/${userId}`);
};
