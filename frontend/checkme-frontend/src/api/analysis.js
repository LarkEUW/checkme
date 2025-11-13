import client from './client.js';

export const createAnalysisJob = async ({ mode, url, storeType, file }) => {
  const formData = new FormData();
  formData.append('mode', mode);
  if (url) formData.append('url', url);
  if (storeType) formData.append('store_type', storeType);
  if (file) formData.append('file', file);

  const { data } = await client.post('/analysis/analyze', formData);
  return data;
};

export const listAnalyses = async (params = {}) => {
  const { data } = await client.get('/analysis/analyses', { params });
  return data;
};

export const getAnalysis = async (analysisId) => {
  const { data } = await client.get(`/analysis/analysis/${analysisId}`);
  return data;
};

export const deleteAnalysis = async (analysisId) => {
  await client.delete(`/analysis/analysis/${analysisId}`);
};
