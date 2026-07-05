import { useState } from 'react';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import DecisionBadge from '../components/DecisionBadge.jsx';
import SafetyFlags from '../components/SafetyFlags.jsx';
import { demoSourceSystems } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

const initialForm = {
  source_system: 'sis',
  source_pk: '',
  name: '',
  email: '',
  phone: '',
  address: '',
  hkid: '',
  emplid: '',
  studentid: '',
  alumniid: '',
  remarks: '',
};

const demoResult = {
  normalized_values: { name: 'john smith', email: 'jsmith@ust.hk', phone: '+8525551234567' },
  decision: 'manual-review',
  confidence: 0.72,
  safety_flags: ['multiple_high_candidates', 'low_score_gap'],
  candidates: [{ golden_id: 'GR-001', score: 0.72 }, { golden_id: 'GR-010', score: 0.65 }],
  next_action: 'Send to manual review queue for steward verification.',
};

export default function IngestionCreate() {
  const [form, setForm] = useState(initialForm);
  const [submitState, setSubmitState] = useState({ loading: false, error: null, result: null });
  const { loading, error, data } = usePageData(() => api.getSourceSystems(), demoSourceSystems, []);
  const sourceSystems = extractArray(data, ['items', 'source_systems'], demoSourceSystems);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitState({ loading: true, error: null, result: null });
    try {
      const result = await api.ingest({
        source_system: form.source_system,
        source_pk: form.source_pk,
        data: {
          name: form.name,
          email: form.email,
          phone: form.phone,
          address: form.address,
          hkid: form.hkid,
          emplid: form.emplid,
          studentid: form.studentid,
          alumniid: form.alumniid,
          remarks: form.remarks,
        },
      });
      setSubmitState({ loading: false, error: null, result });
    } catch (submitError) {
      setSubmitState({ loading: false, error: submitError.message, result: demoResult });
    }
  }

  const result = submitState.result;
  const resultDecision = typeof result?.decision === 'string'
    ? result
    : (result?.decision || {});
  const candidateRows = result?.candidates || (
    resultDecision.best_golden_id
      ? [{ golden_id: resultDecision.best_golden_id, score: resultDecision.confidence }]
      : []
  );

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <h2>Create Source Record</h2>
          <p className="muted-text">Capture an incoming record and see how the IRE classifies it.</p>
        </div>
      </div>
      <ApiStatusBanner error={error || submitState.error} />
      {(loading || submitState.loading) && <div className="card subtle">Loading…</div>}
      <div className="two-col">
        <form className="card form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Source System</span>
            <select value={form.source_system} onChange={(event) => setForm({ ...form, source_system: event.target.value })}>
              {sourceSystems.map((system) => (
                <option key={system.id || system.name} value={system.id || system.name}>{system.name}</option>
              ))}
            </select>
          </label>
          {[
            ['source_pk', 'Source PK'],
            ['name', 'Name'],
            ['email', 'Email'],
            ['phone', 'Phone'],
            ['address', 'Address'],
            ['hkid', 'HKID - Hong Kong Identity Document Number'],
            ['emplid', 'EmplId - Employee Identifier'],
            ['studentid', 'Student ID'],
            ['alumniid', 'Alumni ID'],
          ].map(([key, label]) => (
            <label key={key} className="field">
              <span>{label}</span>
              <input value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
            </label>
          ))}
          <label className="field full-width">
            <span>Raw Payload / Remarks</span>
            <textarea rows="5" value={form.remarks} onChange={(event) => setForm({ ...form, remarks: event.target.value })} />
          </label>
          <div className="button-row">
            <button type="submit" className="button primary">Submit to IRE</button>
          </div>
        </form>
        <div className="card">
          <h3>Resolution result</h3>
          {!result ? (
            <div className="empty-state">Submit a source record to view normalized values, decisioning, and candidate matches.</div>
          ) : (
            <div className="page-stack compact">
              <div><strong>Decision:</strong> <DecisionBadge decision={resultDecision.decision || result.decision} /></div>
              <div><strong>Confidence:</strong> {Math.round(((resultDecision.confidence ?? result.confidence) || 0) * 100)}%</div>
              <div><strong>Safety flags:</strong> <SafetyFlags flags={resultDecision.safety_flags || result.safety_flags || []} /></div>
              <div>
                <strong>Normalized values</strong>
                <pre className="code-block">{JSON.stringify(result.normalized_values || result.source_record?.raw_payload || {}, null, 2)}</pre>
              </div>
              <div>
                <strong>Candidates</strong>
                <ul>
                  {candidateRows.map((candidate) => (
                    <li key={candidate.golden_id}>{candidate.golden_id} · {Math.round((candidate.score || 0) * 100)}%</li>
                  ))}
                </ul>
              </div>
              <div><strong>Next action:</strong> {result.next_action || 'Review the resulting golden record linkage.'}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
