import { Link } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoMatchingRules } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

function normalizeRuleRow(row) {
  return {
    id: row.id || row.rule_id,
    name: row.name || row.rule_name,
    type: row.type || row.rule_type,
    active: row.active ?? row.is_active ?? false,
    version: row.version ?? 1,
    created: row.created || row.created_at || '—',
  };
}

export default function MatchingRuleList() {
  const { loading, error, data } = usePageData(() => api.getMatchingRules(), demoMatchingRules, []);
  const rows = extractArray(data, ['items', 'rules'], demoMatchingRules).map(normalizeRuleRow);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Matching Rules</h2><p className="muted-text">Review deterministic and safety rules that govern record linking.</p></div><Link className="button primary" to="/settings/matching-rules/new">Create new rule</Link></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading matching rules…</div>}
      <div className="card"><div className="table-wrap"><table className="data-table"><thead><tr><th>Name</th><th>Type</th><th>Active</th><th>Version</th><th>Created</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.id || `matching-rule-${index}`}><td><Link to={`/settings/matching-rules/${row.id}`}>{row.name}</Link></td><td>{row.type}</td><td>{row.active ? 'Yes' : 'No'}</td><td>{row.version}</td><td>{row.created}</td></tr>)}</tbody></table></div></div>
    </div>
  );
}
