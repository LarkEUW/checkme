export const sampleMetrics = {
  users: { total: 12, active: 10, admins: 2 },
  analyses: {
    total: 48,
    completed: 39,
    verdicts: {
      safe: 18,
      needs_review: 14,
      high_risk: 5,
      block: 2
    }
  }
};

export const sampleAnalyses = [
  {
    id: 'mock-safe',
    status: 'completed',
    final_score: 8.5,
    verdict: 'safe',
    created_at: new Date().toISOString()
  },
  {
    id: 'mock-review',
    status: 'completed',
    final_score: 22.3,
    verdict: 'needs_review',
    created_at: new Date().toISOString()
  },
  {
    id: 'mock-in-progress',
    status: 'in_progress',
    final_score: null,
    verdict: null,
    created_at: new Date().toISOString()
  }
];
