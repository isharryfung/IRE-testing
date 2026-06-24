import React from 'react';

function fmt(value) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(4);
  return String(value);
}

export default function EvidenceTable({ evidence }) {
  if (!evidence || !evidence.length) {
    return <p className="muted">No feature-level evidence available.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Feature</th>
            <th>Type</th>
            <th>Source Value</th>
            <th>Golden Value</th>
            <th>Algorithm</th>
            <th>Similarity</th>
            <th>Weight</th>
            <th>Weighted</th>
            <th>Conflict</th>
            <th>Blocking</th>
          </tr>
        </thead>
        <tbody>
          {evidence.map((feature, index) => (
            <tr key={feature.feature_id || `${feature.feature_name || 'feature'}-${index}`}>
              <td>{fmt(feature.feature_name)}</td>
              <td>{fmt(feature.feature_type)}</td>
              <td>{fmt(feature.source_value)}</td>
              <td>{fmt(feature.golden_value)}</td>
              <td>{fmt(feature.similarity_algorithm)}</td>
              <td>{fmt(feature.similarity_score)}</td>
              <td>{fmt(feature.weight)}</td>
              <td>{fmt(feature.weighted_score)}</td>
              <td>{fmt(feature.is_conflict)}</td>
              <td>{fmt(feature.is_blocking_feature)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
