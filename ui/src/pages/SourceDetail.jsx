import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client.js';
import { useNavigate, useParams } from 'react-router-dom';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import AuditTimeline from '../components/AuditTimeline.jsx';
import EvidenceTable from '../components/EvidenceTable.jsx';
import { demoGoldenRecords, demoSourceRecords, demoReviewTasks } from './demoData.js';
import { buildEvidence, extractArray, usePageData } from './pageHelpers.js';

function GoldenPickModal({ title, excludeGoldenId, selectedId, onSelectId, onConfirm, onClose, busy, message }) {
  const [allGoldens, setAllGoldens] = useState([]);
  useEffect(() => {
    api.getGoldenRecords({})
      .then((records) => setAllGoldens(Array.isArray(records) ? records : demoGoldenRecords))
      .catch(() => setAllGoldens(demoGoldenRecords));
  }, []);
  const options = allGoldens.filter((g) => g.golden_id !== excludeGoldenId);
  return (
    <div className="modal-overlay">
      <div className="modal-wide">
        <div className="modal-header">
          <h3>{title}</h3>
          <button type="button" className="button" onClick={onClose}>✕ Exit</button>
        </div>
        <label className="field">
          <span>Select golden record</span>
          <select value={selectedId} onChange={(e) => onSelectId(e.target.value)}>
            <option value="">— Choose golden record —</option>
            {options.map((g) => (
              <option key={g.golden_id} value={g.golden_id}>
                {g.golden_id} — {g.canonical_name || g.name || '(no name)'}
              </option>
            ))}
          </select>
        </label>
        {message && <div className="top-gap muted-text">{message}</div>}
        <div className="button-row wrap top-gap">
          <button type="button" className="button" onClick={onClose} disabled={busy}>Exit</button>
          <button type="button" className="button primary" disabled={busy || !selectedId} onClick={() => onConfirm(selectedId)}>
            {busy ? 'Working…' : 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SourceDetail() {
  const { sourceRecordId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('Overview');
  const [refreshKey, setRefreshKey] = useState(0);

  // Action state
  const [modal, setModal] = useState(null); // null | 'link' | 'move'
  const [modalGoldenId, setModalGoldenId] = useState('');
  const [modalBusy, setModalBusy] = useState(false);
  const [modalMessage, setModalMessage] = useState('');
  const [actionBusy, setActionBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

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
    [sourceRecordId, refreshKey]
  );

  const record = data.record?.source_record_id ? data.record : fallback.record;
  const normalized = data.normalized?.normalized ? data.normalized.normalized : data.normalized || fallback.normalized;
  const candidates = extractArray(data.candidates, ['items', 'candidates'], fallback.candidates);
  const history = extractArray(data.history, ['items', 'events'], fallback.history);
  const bestCandidate = candidates[0];
  const rawPayload = record?.raw_payload;
  const rawPayloadText = typeof rawPayload === 'string'
    ? rawPayload
    : JSON.stringify(rawPayload || {}, null, 2);

  function openModal(mode) {
    setModal(mode);
    setModalGoldenId('');
    setModalMessage('');
  }

  async function handleLinkToGolden(goldenId) {
    setModalBusy(true);
    setModalMessage('');
    try {
      await api.linkSourceRecord(sourceRecordId, { golden_id: goldenId, actor: 'steward' });
      setModalMessage(`✓ Linked to golden record ${goldenId}.`);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setModalMessage(`Error: ${err.message}`);
    } finally {
      setModalBusy(false);
    }
  }

  async function handleUnlink() {
    setActionBusy(true);
    setActionMessage('');
    try {
      await api.unlinkSourceRecord(sourceRecordId, { reason: 'Manual unlink by steward', actor: 'steward' });
      setActionMessage(`✓ Unlinked from golden record ${record.linked_golden}.`);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setActionMessage(`Error: ${err.message}`);
    } finally {
      setActionBusy(false);
    }
  }

  async function handleMoveToGolden(goldenId) {
    setModalBusy(true);
    setModalMessage('');
    try {
      await api.linkSourceRecord(sourceRecordId, { golden_id: goldenId, actor: 'steward' });
      setModalMessage(`✓ Moved to golden record ${goldenId}.`);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setModalMessage(`Error: ${err.message}`);
    } finally {
      setModalBusy(false);
    }
  }

  async function handleRematch() {
    setActionBusy(true);
    setActionMessage('');
    try {
      const result = await api.rematchSourceRecord(sourceRecordId);
      const decision = result?.decision || result?.match_decision || 'completed';
      setActionMessage(`✓ Re-run matching completed. Decision: ${decision}.`);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setActionMessage(`Error: ${err.message}`);
    } finally {
      setActionBusy(false);
    }
  }

  async function handleCreateNewGolden() {
    setActionBusy(true);
    setActionMessage('');
    try {
      const result = await api.createGoldenFromSource(sourceRecordId);
      const newGoldenId = result?.golden_id;
      if (newGoldenId) {
        navigate(`/golden/${newGoldenId}`);
      } else {
        setActionMessage('✓ New golden record created.');
        setRefreshKey((k) => k + 1);
      }
    } catch (err) {
      setActionMessage(`Error: ${err.message}`);
    } finally {
      setActionBusy(false);
    }
  }

  return (
    <>
      {modal && (
        <GoldenPickModal
          title={modal === 'link' ? 'Link to Golden Record' : 'Move to Another Golden Record'}
          excludeGoldenId={modal === 'move' ? record.linked_golden : undefined}
          selectedId={modalGoldenId}
          onSelectId={setModalGoldenId}
          onConfirm={modal === 'link' ? handleLinkToGolden : handleMoveToGolden}
          onClose={() => setModal(null)}
          busy={modalBusy}
          message={modalMessage}
        />
      )}
      <div className="page-stack">
        <div className="page-header"><div><h2>Source Record {record.source_record_id}</h2><p className="muted-text">Source system: {record.source_system}</p></div></div>
        <ApiStatusBanner error={error} />
        {loading && <div className="card subtle">Loading source record…</div>}
        <div className="two-col">
          <div className="card"><h3>Raw payload</h3><pre className="code-block">{rawPayloadText}</pre></div>
          <div className="card"><h3>Normalized values</h3><pre className="code-block">{JSON.stringify(normalized || {}, null, 2)}</pre></div>
        </div>
        <div className="card">
          <div><strong>Current linked Golden Record:</strong> {record.linked_golden || 'Not linked'}</div>
          <div className="button-row wrap top-gap">
            <button className="button" disabled={actionBusy} onClick={() => openModal('link')}>Link to Golden</button>
            <button className="button" disabled={actionBusy || !record.linked_golden} onClick={handleUnlink}>Unlink</button>
            <button className="button" disabled={actionBusy} onClick={() => openModal('move')}>Move to Another Golden</button>
            <button className="button" disabled={actionBusy} onClick={handleRematch}>Re-run Matching</button>
            <button className="button" disabled={actionBusy} onClick={handleCreateNewGolden}>Create New Golden</button>
          </div>
          {actionMessage && <div className="top-gap muted-text">{actionMessage}</div>}
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
    </>
  );
}
