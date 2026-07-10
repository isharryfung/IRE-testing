const DECISION_STYLES = {
  'auto-merge': 'success',
  'manual-review': 'warning',
  'new-golden-record': 'info',
  conflict: 'danger',
  accept_merge: 'success',
  reject_candidate: 'danger',
  create_new_golden: 'info',
  escalate: 'warning',
  request_more_info: 'muted',
};

export default function DecisionBadge({ decision }) {
  const decisionValue = typeof decision === 'string'
    ? decision
    : (decision && typeof decision === 'object' ? decision.decision : '');

  if (!decisionValue) {
    return <span className="badge muted">Unknown</span>;
  }

  const label = decisionValue.replace(/[-_]/g, ' ');
  const tone = DECISION_STYLES[decisionValue] || 'muted';
  return <span className={`badge ${tone}`}>{label}</span>;
}
