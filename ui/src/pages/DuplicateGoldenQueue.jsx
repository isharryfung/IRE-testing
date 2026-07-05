import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoDuplicates } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

export default function DuplicateGoldenQueue() {
  const navigate = useNavigate();
  const { loading, error, data } = usePageData(() => api.getDuplicates({}), demoDuplicates, []);
  const rows = extractArray(data, ['items', 'duplicates'], demoDuplicates);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Duplicate Golden Queue</h2><p className="muted-text">Investigate possible duplicate golden profiles before consolidation.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading duplicate golden pairs…</div>}
      <div className="card">
        <div className="table-wrap"><table className="data-table clickable-table"><thead><tr><th>Golden A</th><th>Golden B</th><th>Similarity Score</th><th>Status</th><th>Detection Method</th><th>Created</th></tr></thead><tbody>{rows.map((row) => <tr key={row.duplicate_id} onClick={() => navigate(`/duplicates/${row.duplicate_id}`)}><td>{row.golden_a.golden_id}</td><td>{row.golden_b.golden_id}</td><td>{Math.round((row.similarity_score || 0) * 100)}%</td><td>{row.status}</td><td>{row.detection_method}</td><td>{row.created_at}</td></tr>)}</tbody></table></div>
      </div>
    </div>
  );
}
