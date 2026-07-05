import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoMatchingFeatures } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

function normalizeFeatureRow(row) {
  return {
    id: row.id || row.feature_id,
    feature: row.feature || row.feature_name,
    display_label: row.display_label || row.feature_name || row.feature,
    enabled: row.enabled ?? row.is_enabled ?? false,
    priority: row.priority ?? 0,
    algorithm: row.algorithm || '—',
    auto_merge_eligible: row.auto_merge_eligible ?? row.is_auto_merge_eligible ?? false,
    blocking: row.blocking ?? row.is_blocking ?? false,
    visible_in_review: row.visible_in_review ?? row.is_visible_in_review ?? false,
    feature_type: row.feature_type || 'profile',
    is_manual_review_only: row.is_manual_review_only ?? false,
    is_active: row.is_active ?? true,
  };
}

export default function MatchingFeatureSettings() {
  const { loading, error, data } = usePageData(() => api.getMatchingFeatures(), demoMatchingFeatures, []);
  const rows = extractArray(data, ['items', 'features'], demoMatchingFeatures).map(normalizeFeatureRow);
  const [draftRows, setDraftRows] = useState(rows);
  const [message, setMessage] = useState('');

  useEffect(() => setDraftRows(rows), [rows]);

  const calculatedRows = useMemo(() => {
    const totalPriority = draftRows.reduce((sum, row) => sum + (row.enabled ? Number(row.priority || 0) : 0), 0) || 1;
    return draftRows.map((row) => ({ ...row, calculated_weight: row.enabled ? ((totalPriority - Number(row.priority || 0) + 1) / totalPriority).toFixed(2) : '0.00' }));
  }, [draftRows]);

  async function handleSave() {
    try {
      await Promise.all(calculatedRows.map((row) => api.updateMatchingFeature(row.id, {
        feature_id: row.id,
        feature_name: row.feature,
        display_label: row.display_label,
        feature_type: row.feature_type,
        is_enabled: row.enabled,
        priority: Number(row.priority || 0),
        algorithm: row.algorithm,
        is_auto_merge_eligible: row.auto_merge_eligible,
        is_manual_review_only: row.is_manual_review_only,
        is_blocking: row.blocking,
        is_visible_in_review: row.visible_in_review,
        is_active: row.is_active,
      })));
      setMessage('Feature settings saved.');
    } catch {
      setMessage('Backend unavailable. Changes remain visible for demo use.');
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Matching Features</h2><p className="muted-text">Adjust which features participate in matching and how strongly they contribute.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading matching features…</div>}
      <div className="card">
        <div className="table-wrap"><table className="data-table"><thead><tr><th>Feature</th><th>Display Label</th><th>Enabled</th><th>Priority</th><th>Algorithm</th><th>Auto-merge Eligible</th><th>Blocking</th><th>Visible in Review</th><th>Calculated Weight</th></tr></thead><tbody>{calculatedRows.map((row) => <tr key={row.id}><td>{row.feature}</td><td>{row.display_label}</td><td><input type="checkbox" checked={!!row.enabled} onChange={(event) => setDraftRows(draftRows.map((item) => item.id === row.id ? { ...item, enabled: event.target.checked } : item))} /></td><td><input type="number" value={row.priority} onChange={(event) => setDraftRows(draftRows.map((item) => item.id === row.id ? { ...item, priority: Number(event.target.value) } : item))} /></td><td>{row.algorithm}</td><td>{row.auto_merge_eligible ? 'Yes' : 'No'}</td><td>{row.blocking ? 'Yes' : 'No'}</td><td>{row.visible_in_review ? 'Yes' : 'No'}</td><td>{row.calculated_weight}</td></tr>)}</tbody></table></div>
        <div className="button-row top-gap"><button className="button primary" onClick={handleSave}>Save changes</button>{message && <span className="muted-text">{message}</span>}</div>
      </div>
    </div>
  );
}
