import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoSourceSystems } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

export default function SourceSystemList() {
  const { loading, error, data } = usePageData(() => api.getSourceSystems(), demoSourceSystems, []);
  const rows = extractArray(data, ['items', 'source_systems'], demoSourceSystems);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Source Systems</h2><p className="muted-text">Review trust levels and whether a source is allowed to auto-merge.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading source systems…</div>}
      <div className="card"><div className="table-wrap"><table className="data-table"><thead><tr><th>Name</th><th>Trust Level</th><th>Internal / External</th><th>Auto-merge Allowed</th><th>Status</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id || row.name}><td>{row.name}</td><td>{row.trust_level}</td><td>{row.internal_external}</td><td>{row.auto_merge_allowed ? 'Yes' : 'No'}</td><td>{row.status}</td></tr>)}</tbody></table></div></div>
    </div>
  );
}
