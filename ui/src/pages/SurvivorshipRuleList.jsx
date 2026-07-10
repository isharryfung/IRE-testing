import { Link } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoSurvivorshipRules } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

function normalizeRuleRow(row) {
  return {
    id: row.id || row.rule_id,
    name: row.name || row.rule_name,
    active: row.active ?? row.is_active ?? false,
    version: row.version ?? 1,
    description: row.description || row.strategy || '—',
  };
}

export default function SurvivorshipRuleList() {
  const { loading, error, data } = usePageData(() => api.getSurvivorshipRules(), demoSurvivorshipRules, []);
  const rows = extractArray(data, ['items', 'rules'], demoSurvivorshipRules).map(normalizeRuleRow);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Survivorship Rules</h2><p className="muted-text">Manage how field values are selected when multiple sources contribute to one golden record.</p></div><Link className="button primary" to="/settings/survivorship/new">Create / edit rule</Link></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading survivorship rules…</div>}
      <div className="card"><div className="table-wrap"><table className="data-table"><thead><tr><th>Name</th><th>Active</th><th>Version</th><th>Description</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.id || `survivorship-rule-${index}`}><td><Link to={`/settings/survivorship/${row.id}`}>{row.name}</Link></td><td>{row.active ? 'Yes' : 'No'}</td><td>{row.version}</td><td>{row.description}</td></tr>)}</tbody></table></div></div>
    </div>
  );
}
