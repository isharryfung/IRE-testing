import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import SearchFilters from '../components/SearchFilters.jsx';
import { demoGoldenRecords } from './demoData.js';
import { extractArray, formatDate, usePageData } from './pageHelpers.js';

const filters = [
  { name: 'name', label: 'Name' },
  { name: 'email', label: 'Email' },
  { name: 'phone', label: 'Phone' },
  { name: 'hkid', label: 'HKID' },
  { name: 'emplid', label: 'EmplId' },
  { name: 'studentid', label: 'Student ID' },
  { name: 'alumniid', label: 'Alumni ID' },
  { name: 'status', label: 'Status', type: 'select', options: ['Active', 'Review'] },
  { name: 'person_type', label: 'Person Type', type: 'select', options: ['Staff', 'Student'] },
  { name: 'possible_duplicate', label: 'Possible Duplicate', type: 'select', options: [{ label: 'Yes', value: 'true' }, { label: 'No', value: 'false' }] },
];

export default function GoldenSearch() {
  const [values, setValues] = useState({});
  const navigate = useNavigate();
  const { loading, error, data } = usePageData(() => api.getGoldenRecords(values), demoGoldenRecords, [JSON.stringify(values)]);
  const rows = extractArray(data, ['items', 'records', 'golden_records'], demoGoldenRecords);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Golden Records</h2><p className="muted-text">Search consolidated profiles created by the identity resolution engine.</p></div></div>
      <ApiStatusBanner error={error} />
      <SearchFilters filters={filters} values={values} onChange={(name, value) => setValues({ ...values, [name]: value })} />
      {loading && <div className="card subtle">Searching golden records…</div>}
      <div className="card">
        <div className="table-wrap">
          <table className="data-table clickable-table">
            <thead><tr><th>Golden ID</th><th>Name</th><th>Email</th><th>HKID / EmplID</th><th>Person Type</th><th>Status</th><th>Linked Sources</th><th>Last Updated</th></tr></thead>
            <tbody>
              {rows.length ? rows.map((row) => (
                <tr key={row.golden_id} onClick={() => navigate(`/golden/${row.golden_id}`)}>
                  <td>{row.golden_id}</td><td>{row.canonical_name || row.name}</td><td>{row.email || row.canonical_email || '—'}</td><td>{row.hkid || row.canonical_hkid || row.emplid || row.canonical_emplid || '—'}</td><td>{row.person_type || '—'}</td><td>{row.status || '—'}</td><td>{row.linked_sources ?? 0}</td><td>{formatDate(row.last_updated || row.updated_at)}</td>
                </tr>
              )) : <tr><td colSpan="8" className="empty-cell">No data available.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
