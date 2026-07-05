import { useMemo, useState } from 'react';
import { api } from '../api/client.js';
import { useParams } from 'react-router-dom';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import AuditTimeline from '../components/AuditTimeline.jsx';
import { useRole } from '../components/Layout.jsx';
import { demoAuditEvents, demoGoldenRecords } from './demoData.js';
import { extractArray, formatDate, usePageData } from './pageHelpers.js';

const tabs = ['Overview', 'Linked Sources', 'Field Provenance', 'Match History', 'Merge History', 'Audit Events'];

export default function GoldenDetail() {
  const { goldenId } = useParams();
  const { role } = useRole();
  const [tab, setTab] = useState('Overview');
  const fallback = useMemo(() => {
    const golden = demoGoldenRecords.find((item) => item.golden_id === goldenId) || demoGoldenRecords[0];
    return { golden, sourceLinks: golden.source_links || [], provenance: golden.field_provenance || [], history: golden.history || [], audit: demoAuditEvents };
  }, [goldenId]);

  const { loading, error, data } = usePageData(
    async () => {
      const [golden, sourceLinks, provenance, history, audit] = await Promise.all([
        api.getGoldenRecord(goldenId),
        api.getGoldenSourceLinks(goldenId),
        api.getGoldenFieldProvenance(goldenId),
        api.getGoldenHistory(goldenId),
        api.getAuditEvents({ entity_id: goldenId }),
      ]);
      return { golden, sourceLinks, provenance, history, audit };
    },
    fallback,
    [goldenId]
  );

  const golden = data.golden?.golden_id ? data.golden : fallback.golden;
  const sourceLinks = extractArray(data.sourceLinks, ['items', 'records'], fallback.sourceLinks);
  const provenance = extractArray(data.provenance, ['items', 'fields'], fallback.provenance);
  const history = extractArray(data.history, ['items', 'events'], fallback.history);
  const audit = extractArray(data.audit, ['items', 'events'], fallback.audit);

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>{golden.name}</h2><p className="muted-text">Golden ID: {golden.golden_id}</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading golden record…</div>}
      <div className="two-col">
        <div className="card">
          <h3>Canonical profile</h3>
          <div className="detail-grid">
            {Object.entries({ Email: golden.email, Phone: golden.phone, HKID: golden.hkid, EmplId: golden.emplid, StudentID: golden.studentid, AlumniID: golden.alumniid, Address: golden.address, Status: golden.status, 'Person type': golden.person_type, 'Last updated': formatDate(golden.last_updated) }).map(([label, value]) => (
              <div key={label}><strong>{label}:</strong> {value || '—'}</div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3>Steward actions</h3>
          {role === 'Viewer' ? <div className="empty-state">Viewer role can inspect but cannot change links or survivorship outcomes.</div> : (
            <div className="button-row wrap">
              <button className="button">Link Source Record</button>
              <button className="button">Unlink Source Record</button>
              <button className="button">Apply Field Override</button>
              <button className="button">Flag as Duplicate</button>
              <button className="button">Merge with Another Golden</button>
            </div>
          )}
        </div>
      </div>
      <div className="tab-row">
        {tabs.map((item) => <button key={item} className={`tab ${tab === item ? 'active' : ''}`} onClick={() => setTab(item)}>{item}</button>)}
      </div>
      <div className="card">
        {tab === 'Overview' && <div className="empty-state">Use the tabs to inspect provenance, history, and audit context for this profile.</div>}
        {tab === 'Linked Sources' && <div className="table-wrap"><table className="data-table"><thead><tr><th>Source Record</th><th>Source System</th><th>Source PK</th><th>Status</th></tr></thead><tbody>{sourceLinks.map((row) => <tr key={row.source_record_id}><td>{row.source_record_id}</td><td>{row.source_system}</td><td>{row.source_pk}</td><td>{row.link_status}</td></tr>)}</tbody></table></div>}
        {tab === 'Field Provenance' && <div className="table-wrap"><table className="data-table"><thead><tr><th>Field</th><th>Chosen Value</th><th>Winner Source</th><th>Rule</th></tr></thead><tbody>{provenance.map((row, index) => <tr key={`${row.field}-${index}`}><td>{row.field}</td><td>{row.chosen_value}</td><td>{row.winner_source}</td><td>{row.rule}</td></tr>)}</tbody></table></div>}
        {tab === 'Match History' && <AuditTimeline events={history} />}
        {tab === 'Merge History' && <AuditTimeline events={history.filter((item) => item.event_type?.includes('merge') || item.event_type?.includes('link'))} />}
        {tab === 'Audit Events' && <AuditTimeline events={audit} />}
      </div>
    </div>
  );
}
