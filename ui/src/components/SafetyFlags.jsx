import React from 'react';

export default function SafetyFlags({ flags }) {
  if (!flags || !flags.length) {
    return <p className="muted">No safety flags.</p>;
  }

  return (
    <ul className="chip-list">
      {flags.map((flag) => (
        <li key={flag} className="chip danger">{flag}</li>
      ))}
    </ul>
  );
}
