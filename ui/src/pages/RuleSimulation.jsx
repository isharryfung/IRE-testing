import { useState } from 'react';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoSimulation, demoSourceRecords } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

export default function RuleSimulation() {
  const { loading, error, data } = usePageData(() => api.getSourceRecords({}), demoSourceRecords, []);
  const records = extractArray(data, ['items', 'records'], demoSourceRecords);
  const [selected, setSelected] = useState(records[0]?.source_record_id || 'IN-001');
  const [draft, setDraft] = useState('If source is trusted and email matches exactly, increase confidence by 0.05.');
  const [results, setResults] = useState(null);

  async function handleRun() {
    try {
      const simulation = await api.runSimulation({ source_record_ids: [selected], draft_rules: draft });
      setResults(simulation.results || simulation);
    } catch {
      setResults(demoSimulation.results);
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Rule Simulation</h2><p className="muted-text">Test draft rule changes before promoting them into production settings.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading source records…</div>}
      <div className="two-col">
        <div className="card form-grid">
          <label className="field"><span>Select source record</span><select value={selected} onChange={(event) => setSelected(event.target.value)}>{records.map((record) => <option key={record.source_record_id} value={record.source_record_id}>{record.source_record_id} · {record.name}</option>)}</select></label>
          <label className="field full-width"><span>Draft rule changes</span><textarea rows="8" value={draft} onChange={(event) => setDraft(event.target.value)} /></label>
          <div className="button-row"><button className="button primary" onClick={handleRun}>Run simulation</button></div>
        </div>
        <div className="card">
          <h3>Comparison results</h3>
          {!results ? <div className="empty-state">Run a simulation to compare old and new decisions.</div> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Source Record</th><th>Old Decision</th><th>New Decision</th><th>Notes</th></tr></thead><tbody>{results.map((row) => <tr key={row.source_record_id}><td>{row.source_record_id}</td><td>{row.old_decision}</td><td>{row.new_decision}</td><td>{row.note}</td></tr>)}</tbody></table></div>}
        </div>
      </div>
    </div>
  );
}
