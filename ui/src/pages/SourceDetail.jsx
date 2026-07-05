import { useMemo, useState } from 'react';
import { api } from '../api/client.js';
import { useParams } from 'react-router-dom';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import AuditTimeline from '../components/AuditTimeline.jsx';
import EvidenceTable from '../components/EvidenceTable.jsx';
import { demoSourceRecords, demoReviewTasks } from './demoData.js';
import { buildEvidence, extractArray, usePageData } from './pageHelpers.js';

export default function SourceDetail() {
  const { sourceRecordId } = useParams();
  const [tab, setTab] = useState('Overview');
  const fallback = useMemo(() => {
    const record = demoSourceRecords.find((item) => item.source_record_id === sourceRecordId) || demoSourceRecords[0];
    const review = demoReviewTasks.find((item) => item.source_record.record_id === sourceRecordId);
    const candidates = review?.candidates || [{ golden_id: record.linked_golden, score: 0.72, features: buildEvidence(record, { name: record.name, email: record.email, phone: record.phone, address: record.address }, { name: 0.9, email: 1, phone: 1, address: 0.95 }) }];
    return { record, normalized: record.normalized, candidates, history: review?.history || [] };
  }, [sourceRecordId]);
  const { loading, error, data } = usePageData(
    async () => {
      const [record, normalized, candidates, history] = await Promise.all([
        api.getSourceRecord(sourceRecordId),
        api.getSourceRecordNormalized(sourceRecordId),
        api.getSourceRecordCandidates(sourceRecordId),
        api.getSourceRecordHistory(sourceRecordId),
      ]);
      return { record, normalized, candidates, history };
    },
    fallback,
    [sourceRecordId]
  );

  const record = data.record?.source_record_id ? data.record : fallback.record;
  const normalized = data.normalized?.normalized ? data.normalized.normalized : data.normalized || fallback.normalized;
  const candidates = extractArray(data.candidates, ['items', 'candidates'], fallback.candidates);
  const history = extractArray(data.history, ['items', 'events'], fallback.history);
  const bestCandidate = candidates[0];

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Source Record {record.source_record_id}</h2><p className="muted-text">Source system: {record.source_system}</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading source record…</div>}
      <div className="two-col">
        <div className="card"><h3>Raw payload</h3><pre className="code-block">{record.raw_payload || '{}'}</pre></div>
        <div className="card"><h3>Normalized values</h3><pre className="code-block">{JSON.stringify(normalized || {}, null, 2)}</pre></div>
      </div>
      <div className="card">
        <div><strong>Current linked Golden Record:</strong> {record.linked_golden || 'Not linked'}</div>
        <div className="button-row wrap top-gap"><button className="button">Link to Golden</button><button className="button">Unlink</button><button className="button">Move to Another Golden</button><button className="button">Re-run Matching</button><button className="button">Create New Golden</button></div>
      </div>
      <div className="tab-row"><button className={`tab ${tab === 'Overview' ? 'active' : ''}`} onClick={() => setTab('Overview')}>Overview</button><button className={`tab ${tab === 'History' ? 'active' : ''}`} onClick={() => setTab('History')}>History</button></div>
      <div className="card">
        {tab === 'Overview' ? (
          <>
            <h3>Match candidates</h3>
            <div className="table-wrap"><table className="data-table"><thead><tr><th>Golden</th><th>Name</th><th>Score</th></tr></thead><tbody>{candidates.map((candidate) => <tr key={candidate.golden_id}><td>{candidate.golden_id}</td><td>{candidate.name || candidate.golden_id}</td><td>{Math.round((candidate.score || 0) * 100)}%</td></tr>)}</tbody></table></div>
            <h3>Evidence for best candidate</h3>
            <EvidenceTable features={bestCandidate?.features || []} />
          </>
        ) : <AuditTimeline events={history} />}
      </div>
    </div>
  );
}
