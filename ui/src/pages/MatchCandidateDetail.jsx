import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import DecisionBadge from '../components/DecisionBadge.jsx';
import EvidenceTable from '../components/EvidenceTable.jsx';
import SafetyFlags from '../components/SafetyFlags.jsx';
import { demoMatchCandidates } from './demoData.js';
import { describeStrength, usePageData } from './pageHelpers.js';

export default function MatchCandidateDetail() {
  const { candidateId } = useParams();
  const fallback = useMemo(() => demoMatchCandidates.find((item) => item.candidate_id === candidateId) || demoMatchCandidates[0], [candidateId]);
  const { loading, error, data } = usePageData(
    async () => {
      const [candidate, features] = await Promise.all([api.getMatchCandidate(candidateId), api.getMatchCandidateFeatures(candidateId)]);
      return { ...(candidate || {}), features: features?.features || features };
    },
    fallback,
    [candidateId]
  );
  const candidate = data.candidate_id ? data : fallback;
  const score = Number(candidate.total_score || 0);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Match Candidate {candidate.candidate_id}</h2><p className="muted-text">Plain-English explanation of the scoring outcome.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading candidate detail…</div>}
      <div className="card">
        <p>
          <strong>{describeStrength(score)}</strong> because the source record shares the strongest agreement on the highest-priority identifiers and contact fields.
          {score < 0.5 ? ' A reviewer should likely create a new golden record.' : score < 0.85 ? ' A human should confirm the merge.' : ' The profile is likely safe to merge automatically if no blocking conflicts exist.'}
        </p>
        <div className="detail-grid">
          <div><strong>Source Record:</strong> {candidate.source_record?.record_id || candidate.source_record?.source_record_id}</div>
          <div><strong>Candidate Golden:</strong> {candidate.golden_record?.golden_id || candidate.golden_record?.record_id}</div>
          <div><strong>Total Score:</strong> {Math.round(score * 100)}%</div>
          <div><strong>Decision:</strong> <DecisionBadge decision={candidate.decision} /></div>
        </div>
        <div className="top-gap"><strong>Safety Flags:</strong> <SafetyFlags flags={candidate.safety_flags || []} /></div>
      </div>
      <div className="card"><EvidenceTable features={candidate.features || []} /></div>
      <div className="card">
        <strong>Labels:</strong> Strong match (&gt;85%), Possible match (50-85%), Weak match (&lt;50%), Conflict found.
      </div>
    </div>
  );
}
