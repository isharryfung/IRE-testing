import React from 'react';

const LABELS = {
  'auto-merge': 'Auto Merge',
  'manual-review': 'Manual Review',
  'new-golden-record': 'Create New Golden',
  accept_merge: 'Accept Merge',
  reject_candidate: 'Reject Candidate',
  create_new_golden: 'Create New Golden',
  escalate: 'Escalate',
};

export default function DecisionBadge({ decision }) {
  if (!decision) {
    return <span className="badge neutral">N/A</span>;
  }

  let className = 'neutral';
  if (decision.includes('auto') || decision.includes('accept')) className = 'good';
  if (decision.includes('manual') || decision.includes('escalate')) className = 'warn';
  if (decision.includes('reject') || decision.includes('new-golden')) className = 'info';

  return <span className={`badge ${className}`}>{LABELS[decision] || decision}</span>;
}
