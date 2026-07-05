import { Link } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoSourceRecords } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

const demoBatches = [
  { batch_id: 'BATCH-2025-04-001', source_system: 'HRMS', status: 'Completed', total: 320, processed: 320, auto_merged: 264, manual_review: 28, new_golden: 26, created: '2025-04-10T08:00:00Z' },
  { batch_id: 'BATCH-2025-04-002', source_system: 'Alumni CRM', status: 'Running', total: 180, processed: 124, auto_merged: 72, manual_review: 31, new_golden: 20, created: '2025-04-10T09:00:00Z' },
];

export default function IngestionBatchList() {
  const { loading, error, data } = usePageData(() => api.getBatches(), demoBatches, []);
  const rows = extractArray(data, ['items', 'batches'], demoBatches.length ? demoBatches : demoSourceRecords);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Ingestion Batches</h2><p className="muted-text">Monitor batch-level processing and downstream outcomes.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading batches…</div>}
      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Batch ID</th><th>Source System</th><th>Status</th><th>Total</th><th>Processed</th><th>Auto-merged</th><th>Manual Review</th><th>New Golden</th><th>Created</th></tr></thead>
            <tbody>
              {rows.length ? rows.map((row) => (
                <tr key={row.batch_id || row.source_record_id}>
                  <td><Link to={`/ingestion/batches/${row.batch_id || 'BATCH-DEMO'}`}>{row.batch_id || 'BATCH-DEMO'}</Link></td>
                  <td>{row.source_system}</td><td>{row.status}</td><td>{row.total ?? 1}</td><td>{row.processed ?? 1}</td><td>{row.auto_merged ?? 0}</td><td>{row.manual_review ?? 0}</td><td>{row.new_golden ?? 0}</td><td>{row.created || row.created_at}</td>
                </tr>
              )) : <tr><td colSpan="9" className="empty-cell">No data available.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
