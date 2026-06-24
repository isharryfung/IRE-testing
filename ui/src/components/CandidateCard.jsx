import React from 'react';
import DecisionBadge from './DecisionBadge.jsx';

export default function CandidateCard({ candidate }) {
  const goldenId = candidate?.golden_id || candidate?.candidate_golden_id || candidate?.id;
  return (
    <div className="card">
      <h4>{goldenId || 'Candidate'}</h4>
      {'overall_score' in (candidate || {}) && <p><strong>Score:</strong> {candidate.overall_score}</p>}
      {'confidence' in (candidate || {}) && <p><strong>Confidence:</strong> {candidate.confidence}</p>}
      {'deterministic_result' in (candidate || {}) && <p><strong>Rule:</strong> {candidate.deterministic_result || '—'}</p>}
      {'decision' in (candidate || {}) && <p><strong>Decision:</strong> <DecisionBadge decision={candidate.decision} /></p>}
      {candidate?.canonical_name && <p><strong>Name:</strong> {candidate.canonical_name}</p>}
      {candidate?.canonical_email && <p><strong>Email:</strong> {candidate.canonical_email}</p>}
      {candidate?.canonical_phone && <p><strong>Phone:</strong> {candidate.canonical_phone}</p>}
    </div>
  );
}
