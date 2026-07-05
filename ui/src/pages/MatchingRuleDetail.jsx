import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoMatchingRules } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

export default function MatchingRuleDetail() {
  const { ruleId } = useParams();
  const fallbackRule = useMemo(() => demoMatchingRules.find((item) => item.id === ruleId) || { id: 'new', name: '', type: 'Deterministic', active: true, version: 1, created: 'Draft', description: '' }, [ruleId]);
  const { loading, error, data } = usePageData(() => api.getMatchingRules(), demoMatchingRules, [ruleId]);
  const rules = extractArray(data, ['items', 'rules'], demoMatchingRules);
  const rule = rules.find((item) => item.id === ruleId) || fallbackRule;
  const [form, setForm] = useState(rule);
  const versionHistory = [rule, ...rules.filter((item) => item.id !== rule.id).slice(0, 2)].map((item, index) => ({ ...item, version: Math.max((item.version || 1) - index, 1) }));

  async function handleSave(event) {
    event.preventDefault();
    try {
      if (ruleId === 'new') {
        await api.createMatchingRule(form);
      } else {
        await api.updateMatchingRule(ruleId, form);
      }
      alert('Rule saved.');
    } catch {
      alert('Backend unavailable. Draft remains on screen for demo purposes.');
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>{ruleId === 'new' ? 'Create Matching Rule' : `Rule ${ruleId}`}</h2><p className="muted-text">Define the decision logic that determines matching outcomes.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading rule…</div>}
      <div className="two-col">
        <form className="card form-grid" onSubmit={handleSave}>
          <label className="field"><span>Name</span><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label className="field"><span>Type</span><select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })}><option>Deterministic</option><option>Safety</option><option>Scoring</option></select></label>
          <label className="field"><span>Active</span><select value={String(form.active)} onChange={(event) => setForm({ ...form, active: event.target.value === 'true' })}><option value="true">Yes</option><option value="false">No</option></select></label>
          <label className="field full-width"><span>Rule details</span><textarea rows="7" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
          <div className="button-row"><button type="submit" className="button primary">Save Rule</button></div>
        </form>
        <div className="card">
          <h3>Version history</h3>
          <ul>{versionHistory.map((item, index) => <li key={`${item.id}-${index}`}>v{item.version} · {item.name} · {item.active ? 'Active' : 'Inactive'}</li>)}</ul>
        </div>
      </div>
    </div>
  );
}
