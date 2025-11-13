import client from './client.js';

export const listSettings = async () => {
  const { data } = await client.get('/admin/settings');
  return data;
};

export const upsertSetting = async (key, payload) => {
  const { data } = await client.put(`/admin/settings/${key}`, payload);
  return data;
};

export const createSetting = async (payload) => {
  const { data } = await client.post('/admin/settings', payload);
  return data;
};

export const deleteSetting = async (key) => {
  await client.delete(`/admin/settings/${key}`);
};

export const listApiKeys = async () => {
  const { data } = await client.get('/admin/api-keys');
  return data;
};

export const createApiKey = async (payload) => {
  const { data } = await client.post('/admin/api-keys', payload);
  return data;
};

export const toggleApiKey = async (keyId) => {
  const { data } = await client.put(`/admin/api-keys/${keyId}/toggle`);
  return data;
};

export const deleteApiKey = async (keyId) => {
  await client.delete(`/admin/api-keys/${keyId}`);
};

export const getMetrics = async () => {
  const { data } = await client.get('/admin/metrics');
  return data;
};
