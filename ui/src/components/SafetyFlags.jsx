const FLAG_STYLES = {
  tier1_conflict: 'danger',
  multiple_high_candidates: 'orange',
  low_score_gap: 'warning',
  untrusted_source: 'muted',
};

export default function SafetyFlags({ flags = [] }) {
  if (!flags.length) {
    return <span className="muted-text">No safety flags.</span>;
  }

  return (
    <div className="pill-list">
      {flags.map((flag) => (
        <span key={flag} className={`badge ${FLAG_STYLES[flag] || 'muted'}`}>
          {flag.replace(/_/g, ' ')}
        </span>
      ))}
    </div>
  );
}
