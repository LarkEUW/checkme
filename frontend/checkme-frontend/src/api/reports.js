import client from './client.js';

export const addComment = async (analysisId, content) => {
  const { data } = await client.post(`/reports/analysis/${analysisId}/comments`, { content });
  return data;
};

export const getComments = async (analysisId) => {
  const { data } = await client.get(`/reports/analysis/${analysisId}/comments`);
  return data;
};

export const addDecision = async (analysisId, { decision, reason }) => {
  const { data } = await client.post(`/reports/analysis/${analysisId}/decisions`, {
    decision,
    reason
  });
  return data;
};

export const getDecisions = async (analysisId) => {
  const { data } = await client.get(`/reports/analysis/${analysisId}/decisions`);
  return data;
};
