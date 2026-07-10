import { useState } from 'react';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoGoldenRecords } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

const demoPreview = {
  current: { email: 'jchan@example.com', phone: '+85291234567', address: 'Kowloon Tong' },
  preview: { email: 'jchan@example.com', phone: '+85291234567', address: 'Kowloon Tong' },
  reasons: [
    { field: 'email', reason: 'HRMS wins because it is marked as the most trusted source.' },
    { field: 'phone', reason: 'Latest verified value preserved from alumni feed.' },
  ],
};

export default function SurvivorshipPreview() {
  const { loading, error, data } = usePageData(() => api.getGoldenRecords({}), demoGoldenRecords, []);
  const goldens = extractArray(data, ['items', 'records', 'golden_records'], demoGoldenRecords);
  const [selected, setSelected] = useState(goldens[0]?.golden_id || 'GR-001');
  const [preview, setPreview] = useState(null);

  async function handlePreview() {
    try {
      const result = await api.survivorshipPreview({ golden_id: selected });
      setPreview(result);
    } catch {
      setPreview(demoPreview);
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Survivorship Preview</h2><p className="muted-text">Preview how survivorship rules would shape a golden profile before applying changes.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading golden records…</div>}
      <div className="two-col">
        <div className="card form-grid">
          <label className="field"><span>Select a Golden Record</span><select value={selected} onChange={(event) => setSelected(event.target.value)}>{goldens.map((golden) => <option key={golden.golden_id} value={golden.golden_id}>{golden.golden_id} · {golden.canonical_name || golden.name}</option>)}</select></label>
          <div className="button-row"><button className="button primary" onClick={handlePreview}>Preview survivorship</button></div>
        </div>
        <div className="card">
          {!preview ? <div className="empty-state">Choose a golden record to see current values and the rule-driven outcome.</div> : (
            <div className="page-stack compact">
              <div><strong>Current values</strong><pre className="code-block">{JSON.stringify(preview.current || {}, null, 2)}</pre></div>
              <div><strong>Preview values</strong><pre className="code-block">{JSON.stringify(preview.preview || {}, null, 2)}</pre></div>
              <div><strong>Reasons</strong><ul>{(preview.reasons || []).map((item) => <li key={item.field}>{item.field}: {item.reason}</li>)}</ul></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
