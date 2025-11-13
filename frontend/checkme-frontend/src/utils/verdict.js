const VERDICT_META = {
  safe: { label: 'SAFE', className: 'safe' },
  needs_review: { label: 'NEEDS REVIEW', className: 'needs-review' },
  high_risk: { label: 'HIGH RISK', className: 'high-risk' },
  block: { label: 'BLOCK / MALICIOUS', className: 'block' }
};

export const getVerdictMeta = (verdict) => {
  if (!verdict) return VERDICT_META.safe;
  const key = verdict.toLowerCase();
  return VERDICT_META[key] ?? VERDICT_META.safe;
};

export const formatVerdictLabel = (verdict) => getVerdictMeta(verdict).label;
