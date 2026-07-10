import { useState } from 'react';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import AuditTimeline from '../components/AuditTimeline.jsx';
import SearchFilters from '../components/SearchFilters.jsx';
import { demoAuditEvents } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

const filters = [
  { name: 'entity_type', label: 'Entity Type' },
  { name: 'entity_id', label: 'Entity ID' },
  { name: 'event_type', label: 'Event Type' },
  { name: 'start_date', label: 'Start Date', type: 'date' },
  { name: 'end_date', label: 'End Date', type: 'date' },
];

export default function AuditHistory() {
  const [values, setValues] = useState({});
  const { loading, error, data } = usePageData(() => api.getAuditEvents(values), demoAuditEvents, [JSON.stringify(values)]);
  const events = extractArray(data, ['items', 'events'], demoAuditEvents);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Audit History</h2><p className="muted-text">Search resolution events by entity and time window.</p></div></div>
      <ApiStatusBanner error={error} />
      <SearchFilters filters={filters} values={values} onChange={(name, value) => setValues({ ...values, [name]: value })} />
      {loading && <div className="card subtle">Loading audit events…</div>}
      <AuditTimeline events={events} />
    </div>
  );
}
