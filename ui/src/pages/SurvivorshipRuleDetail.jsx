import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoSurvivorshipRules } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

function normalizeRuleRow(row) {
  return {
    id: row.id || row.rule_id,
    name: row.name || row.rule_name || '',
    active: row.active ?? row.is_active ?? true,
    version: row.version ?? 1,
    description: row.description || row.strategy || '',
  };
}

export default function SurvivorshipRuleDetail() {
  const { ruleId } = useParams();
  const fallback = useMemo(() => demoSurvivorshipRules.find((item) => item.id === ruleId) || { id: 'new', name: '', active: true, version: 1, description: '' }, [ruleId]);
  const { loading, error, data } = usePageData(() => api.getSurvivorshipRules(), demoSurvivorshipRules, [ruleId]);
  const rows = useMemo(
    () => extractArray(data, ['items', 'rules'], demoSurvivorshipRules).map(normalizeRuleRow),
    [data],
  );
  const [form, setForm] = useState(fallback);

  useEffect(() => {
    const matchedRule = rows.find((item) => item.id === ruleId);
    setForm(matchedRule || fallback);
  }, [rows, ruleId, fallback]);

  async function handleSave(event) {
    event.preventDefault();
    try {
      if (ruleId === 'new') {
        await api.createSurvivorshipRule(form);
      } else {
        await api.updateSurvivorshipRule(ruleId, form);
      }
      alert('Survivorship rule saved.');
    } catch {
      alert('Backend unavailable. Draft retained locally.');
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>{ruleId === 'new' ? 'Create Survivorship Rule' : `Survivorship Rule ${ruleId}`}</h2><p className="muted-text">Define which source wins for each field family.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading rule…</div>}
      <form className="card form-grid narrow" onSubmit={handleSave}>
        <label className="field"><span>Name</span><input value={form.name || ''} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label className="field"><span>Active</span><select value={String(form.active ?? true)} onChange={(event) => setForm({ ...form, active: event.target.value === 'true' })}><option value="true">Yes</option><option value="false">No</option></select></label>
        <label className="field full-width"><span>Rule logic</span><textarea rows="7" value={form.description || ''} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
        <div className="button-row"><button type="submit" className="button primary">Save Rule</button></div>
      </form>
    </div>
  );
}
