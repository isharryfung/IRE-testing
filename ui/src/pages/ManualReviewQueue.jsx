import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import SearchFilters from '../components/SearchFilters.jsx';
import { demoReviewTasks } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

const filters = [
  { name: 'status', label: 'Status', type: 'select', options: ['pending', 'approved', 'rejected'] },
  { name: 'priority', label: 'Priority', type: 'select', options: ['High', 'Medium', 'Low'] },
  { name: 'reason_code', label: 'Reason Code', type: 'select', options: ['tier1_conflict', 'multiple_candidates', 'low_confidence'] },
];

export default function ManualReviewQueue() {
  const [values, setValues] = useState({});
  const navigate = useNavigate();
  const { loading, error, data } = usePageData(() => api.getReviewTasks(values), demoReviewTasks, [JSON.stringify(values)]);
  const rows = extractArray(data, ['items', 'tasks'], demoReviewTasks);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Manual Review Queue</h2><p className="muted-text">Review open and assigned tasks that need steward attention.</p></div></div>
      <ApiStatusBanner error={error} />
      <SearchFilters filters={filters} values={values} onChange={(name, value) => setValues({ ...values, [name]: value })} />
      {loading && <div className="card subtle">Loading manual review queue…</div>}
      <div className="card">
        <div className="table-wrap">
          <table className="data-table clickable-table">
            <thead><tr><th>Task ID</th><th>Source Record</th><th>Reason</th><th>Best Score</th><th>Priority</th><th>Status</th><th>Assigned To</th><th>Created At</th></tr></thead>
            <tbody>
              {rows.length ? rows.map((row) => (
                <tr key={row.task_id} onClick={() => navigate(`/manual-review/${row.task_id}`)}>
                  <td>{row.task_id}</td><td>{row.source_record.record_id}</td><td><span className="badge warning">{row.reason_code?.replace(/_/g, ' ') || 'manual review'}</span></td><td>{Math.round((row.confidence || 0) * 100)}%</td><td>{row.priority}</td><td>{row.status}</td><td>{row.assigned_to}</td><td>{row.created_at}</td>
                </tr>
              )) : <tr><td colSpan="8" className="empty-cell">No data available.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
