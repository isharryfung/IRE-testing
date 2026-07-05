import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import SearchFilters from '../components/SearchFilters.jsx';
import { demoSourceRecords } from './demoData.js';
import { extractArray, formatDate, usePageData } from './pageHelpers.js';

const filters = [
  { name: 'source_system', label: 'Source System' },
  { name: 'name', label: 'Name' },
  { name: 'email', label: 'Email' },
  { name: 'hkid', label: 'HKID' },
  { name: 'linked_status', label: 'Linked Status', type: 'select', options: ['Linked', 'Not linked'] },
  { name: 'ingestion_status', label: 'Ingestion Status', type: 'select', options: ['Auto merged', 'Manual review', 'New golden'] },
];

export default function SourceSearch() {
  const [values, setValues] = useState({});
  const navigate = useNavigate();
  const { loading, error, data } = usePageData(() => api.getSourceRecords(values), demoSourceRecords, [JSON.stringify(values)]);
  const rows = extractArray(data, ['items', 'records', 'source_records'], demoSourceRecords);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Source Records</h2><p className="muted-text">Search individual source records and inspect their normalization outcomes.</p></div></div>
      <ApiStatusBanner error={error} />
      <SearchFilters filters={filters} values={values} onChange={(name, value) => setValues({ ...values, [name]: value })} />
      {loading && <div className="card subtle">Searching source records…</div>}
      <div className="card">
        <div className="table-wrap">
          <table className="data-table clickable-table">
            <thead><tr><th>Source ID</th><th>Source System</th><th>Source PK</th><th>Name</th><th>Email</th><th>Status</th><th>Linked Golden</th><th>Created</th></tr></thead>
            <tbody>
              {rows.length ? rows.map((row) => (
                <tr key={row.source_record_id} onClick={() => navigate(`/sources/${row.source_record_id}`)}>
                  <td>{row.source_record_id}</td><td>{row.source_system}</td><td>{row.source_pk}</td><td>{row.name}</td><td>{row.email || '—'}</td><td>{row.status}</td><td>{row.linked_golden || 'Not linked'}</td><td>{formatDate(row.created_at)}</td>
                </tr>
              )) : <tr><td colSpan="8" className="empty-cell">No data available.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
