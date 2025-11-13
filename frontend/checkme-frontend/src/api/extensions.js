import client from './client.js';

export const listExtensions = async (params = {}) => {
  const { data } = await client.get('/extensions/', { params });
  return data;
};

export const getExtension = async (extensionId) => {
  const { data } = await client.get(`/extensions/${extensionId}`);
  return data;
};
