function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return '—';
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function rowTone(feature) {
  const flags = feature.flags || [];
  if (flags.includes('conflict')) return 'evidence-row conflict';
  if ((feature.similarity ?? 0) >= 0.85) return 'evidence-row match';
  return 'evidence-row neutral';
}

export default function EvidenceTable({ features = [] }) {
  if (!features.length) {
    return <div className="empty-state">No feature-level evidence available.</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Feature</th>
            <th>Source Value</th>
            <th>Golden Value</th>
            <th>Algorithm</th>
            <th>Similarity</th>
            <th>Priority</th>
            <th>Weight</th>
            <th>Weighted Score</th>
            <th>Flags</th>
          </tr>
        </thead>
        <tbody>
          {features.map((feature, index) => (
            <tr key={`${feature.feature || 'feature'}-${index}`} className={rowTone(feature)}>
              <td>{feature.feature || '—'}</td>
              <td>{feature.source_value || '—'}</td>
              <td>{feature.golden_value || '—'}</td>
              <td>{feature.algorithm || '—'}</td>
              <td>{formatPercent(feature.similarity)}</td>
              <td>{feature.priority ?? '—'}</td>
              <td>{feature.weight ?? '—'}</td>
              <td>{feature.weighted_score != null ? Number(feature.weighted_score).toFixed(2) : '—'}</td>
              <td>{(feature.flags || []).join(', ') || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
