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
  if (!decision) {
    return <span className="badge muted">Unknown</span>;
  }

  const label = decision.replace(/[-_]/g, ' ');
  const tone = DECISION_STYLES[decision] || 'muted';
  return <span className={`badge ${tone}`}>{label}</span>;
}
