import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoDuplicates } from './demoData.js';
import { usePageData } from './pageHelpers.js';

const compareFields = ['name', 'email', 'phone', 'studentid', 'address'];

export default function GoldenMergeReview() {
  const { duplicateId } = useParams();
  const fallback = useMemo(() => demoDuplicates.find((item) => item.duplicate_id === duplicateId) || demoDuplicates[0], [duplicateId]);
  const { loading, error, data } = usePageData(() => api.getDuplicate(duplicateId), fallback, [duplicateId]);
  const duplicate = data.duplicate_id ? data : fallback;

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Golden Merge Review {duplicate.duplicate_id}</h2><p className="muted-text">Compare two possible duplicate golden profiles side by side.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading duplicate pair…</div>}
      <div className="two-col">
        <div className="card"><h3>{duplicate.golden_a.golden_id}</h3><pre className="code-block">{JSON.stringify(duplicate.golden_a, null, 2)}</pre></div>
        <div className="card"><h3>{duplicate.golden_b.golden_id}</h3><pre className="code-block">{JSON.stringify(duplicate.golden_b, null, 2)}</pre></div>
      </div>
      <div className="card">
        <h3>Field comparison</h3>
        <div className="table-wrap"><table className="data-table"><thead><tr><th>Field</th><th>Golden A</th><th>Golden B</th></tr></thead><tbody>{compareFields.map((field) => <tr key={field}><td>{field}</td><td>{duplicate.golden_a[field] || '—'}</td><td>{duplicate.golden_b[field] || '—'}</td></tr>)}</tbody></table></div>
      </div>
      <div className="card">
        <h3>Conflict warnings</h3>
        <ul>{(duplicate.warnings || []).map((warning) => <li key={warning}>{warning}</li>)}</ul>
        <div className="button-row wrap"><button className="button primary">Merge A into B</button><button className="button primary">Merge B into A</button><button className="button">Keep Both</button><button className="button">Escalate</button></div>
      </div>
    </div>
  );
}
