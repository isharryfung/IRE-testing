import { useEffect, useState } from 'react';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoThresholds } from './demoData.js';
import { usePageData } from './pageHelpers.js';

export default function ThresholdSettings() {
  const { loading, error, data } = usePageData(() => api.getThresholds(), demoThresholds, []);
  const [form, setForm] = useState(demoThresholds);
  const [message, setMessage] = useState('');

  useEffect(() => setForm({
    auto_merge_threshold: data.auto_merge_threshold ?? demoThresholds.auto_merge_threshold,
    manual_review_threshold: data.manual_review_threshold ?? demoThresholds.manual_review_threshold,
    multi_match_gap_threshold: data.multi_match_gap_threshold ?? demoThresholds.multi_match_gap_threshold,
  }), [data]);

  async function handleSave(event) {
    event.preventDefault();
    try {
      await api.updateThresholds(form);
      setMessage('Thresholds saved.');
    } catch {
      setMessage('Backend unavailable. Demo values kept locally.');
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Threshold Settings</h2><p className="muted-text">Tune how aggressively the engine auto-merges or requests a human review.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading thresholds…</div>}
      <form className="card form-grid narrow" onSubmit={handleSave}>
        <label className="field"><span>Auto-merge threshold</span><input type="number" step="0.01" value={form.auto_merge_threshold} onChange={(event) => setForm({ ...form, auto_merge_threshold: Number(event.target.value) })} /><small>Default 0.85. Matches above this value can merge automatically if no blocking issues exist.</small></label>
        <label className="field"><span>Manual review threshold</span><input type="number" step="0.01" value={form.manual_review_threshold} onChange={(event) => setForm({ ...form, manual_review_threshold: Number(event.target.value) })} /><small>Default 0.50. Matches below this threshold usually create a new golden record.</small></label>
        <label className="field"><span>Multi-match gap threshold</span><input type="number" step="0.01" value={form.multi_match_gap_threshold} onChange={(event) => setForm({ ...form, multi_match_gap_threshold: Number(event.target.value) })} /><small>Default 0.10. If two candidates are closer than this gap, route to manual review.</small></label>
        <div className="button-row"><button type="submit" className="button primary">Save</button>{message && <span className="muted-text">{message}</span>}</div>
      </form>
    </div>
  );
}
