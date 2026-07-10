import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import { demoSourceRecords } from './demoData.js';
import { extractArray, extractObject, usePageData } from './pageHelpers.js';

const demoBatch = {
  batch: { batch_id: 'BATCH-2025-04-001', source_system: 'HRMS', status: 'Completed', total: 320, processed: 320, auto_merged: 264, manual_review: 28, new_golden: 26, created: '2025-04-10T08:00:00Z' },
  records: demoSourceRecords,
};

export default function IngestionBatchDetail() {
  const { batchId } = useParams();
  const { loading, error, data } = usePageData(
    async () => {
      const [batch, records] = await Promise.all([api.getBatch(batchId), api.getBatchRecords(batchId)]);
      return { batch, records };
    },
    demoBatch,
    [batchId]
  );
  const batch = extractObject(data.batch, ['batch'], demoBatch.batch);
  const records = extractArray(data.records, ['items', 'records'], demoBatch.records);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Batch Detail</h2><p className="muted-text">Review summary and downstream results for {batchId}.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading batch detail…</div>}
      <div className="metric-grid">
        {[
          ['Status', batch.status],
          ['Total', batch.total],
          ['Processed', batch.processed],
          ['Auto-merged', batch.auto_merged],
          ['Manual Review', batch.manual_review],
          ['New Golden', batch.new_golden],
        ].map(([label, value]) => <div key={label} className="card metric-card"><div className="metric-value">{value}</div><div className="muted-text">{label}</div></div>)}
      </div>
      <div className="card">
        <h3>Records in batch</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Source ID</th><th>Name</th><th>Status</th><th>Linked Golden</th><th>Created</th></tr></thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.source_record_id || record.record_id}><td>{record.source_record_id || record.record_id}</td><td>{record.name}</td><td>{record.status}</td><td>{record.linked_golden || 'New golden'}</td><td>{record.created_at}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
