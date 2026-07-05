import { Link } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoMatchingRules } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

export default function MatchingRuleList() {
  const { loading, error, data } = usePageData(() => api.getMatchingRules(), demoMatchingRules, []);
  const rows = extractArray(data, ['items', 'rules'], demoMatchingRules);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Matching Rules</h2><p className="muted-text">Review deterministic and safety rules that govern record linking.</p></div><Link className="button primary" to="/settings/matching-rules/new">Create new rule</Link></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading matching rules…</div>}
      <div className="card"><div className="table-wrap"><table className="data-table"><thead><tr><th>Name</th><th>Type</th><th>Active</th><th>Version</th><th>Created</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td><Link to={`/settings/matching-rules/${row.id}`}>{row.name}</Link></td><td>{row.type}</td><td>{row.active ? 'Yes' : 'No'}</td><td>{row.version}</td><td>{row.created}</td></tr>)}</tbody></table></div></div>
    </div>
  );
}
