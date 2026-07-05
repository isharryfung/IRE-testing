import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client.js';
import { useNavigate, useParams } from 'react-router-dom';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import AuditTimeline from '../components/AuditTimeline.jsx';
import { useRole } from '../components/Layout.jsx';
import { demoAuditEvents, demoGoldenRecords, demoSourceRecords } from './demoData.js';
import { extractArray, formatDate, usePageData } from './pageHelpers.js';

const tabs = ['Overview', 'Linked Sources', 'Field Provenance', 'Match History', 'Merge History', 'Audit Events'];

function GoldenSummary({ golden }) {
  if (!golden) return <div className="muted-text">No record selected.</div>;
  return (
    <div className="detail-grid">
      {[
        ['Golden ID', golden.golden_id],
        ['Name', golden.canonical_name || golden.name],
        ['Email', golden.canonical_email || golden.email],
        ['Phone', golden.canonical_phone || golden.phone],
        ['HKID', golden.canonical_hkid || golden.hkid],
        ['EmplId', golden.canonical_emplid || golden.emplid],
        ['Status', golden.status],
        ['Person Type', golden.person_type],
      ].map(([label, value]) => (
        <div key={label}><strong>{label}:</strong> {value || '—'}</div>
      ))}
    </div>
  );
}

function GoldenPickModal({ title, currentGolden, allGoldens, selectedId, onSelectId, onClose, onAction, actionButtons, busy, message }) {
  const others = allGoldens.filter((g) => g.golden_id !== currentGolden?.golden_id);
  const selectedGolden = others.find((g) => g.golden_id === selectedId) || null;
  return (
    <div className="modal-overlay">
      <div className="modal-wide">
        <div className="modal-header">
          <h3>{title}</h3>
          <button type="button" className="button" onClick={onClose}>✕ Exit</button>
        </div>
        <div className="two-col">
          <div>
            <h4 className="muted-text">Left: Current Golden Record</h4>
            <GoldenSummary golden={currentGolden} />
          </div>
          <div>
            <h4 className="muted-text">Right: Other Golden Record</h4>
            <label className="field">
              <span>Select golden record</span>
              <select value={selectedId} onChange={(e) => onSelectId(e.target.value)}>
                <option value="">— Choose golden record —</option>
                {others.map((g) => (
                  <option key={g.golden_id} value={g.golden_id}>
                    {g.golden_id} — {g.canonical_name || g.name || '(no name)'}
                  </option>
                ))}
              </select>
            </label>
            {selectedGolden && <div className="top-gap"><GoldenSummary golden={selectedGolden} /></div>}
          </div>
        </div>
        {message && <div className="top-gap muted-text">{message}</div>}
        <div className="button-row wrap top-gap">
          <button type="button" className="button" onClick={onClose} disabled={busy}>Exit</button>
          {actionButtons.map(({ key, label, primary, requiresSelection }) => (
            <button
              key={key}
              type="button"
              className={`button${primary ? ' primary' : ''}`}
              disabled={busy || (requiresSelection && !selectedId)}
              onClick={() => onAction(key, selectedId)}
            >
              {busy ? 'Working…' : label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function GoldenDetail() {
  const { goldenId } = useParams();
  const navigate = useNavigate();
  const { role } = useRole();
  const [tab, setTab] = useState('Overview');
  const [refreshKey, setRefreshKey] = useState(0);

  // Linked Sources interactive state
  const [linkMode, setLinkMode] = useState('none'); // 'none' | 'link' | 'unlink'
  const [linkSearch, setLinkSearch] = useState('');
  const [linkResults, setLinkResults] = useState(null);
  const [linkBusy, setLinkBusy] = useState(false);
  const [linkMessage, setLinkMessage] = useState('');

  // Modal state (shared by duplicate + merge modals)
  const [modal, setModal] = useState(null); // null | 'duplicate' | 'merge'
  const [allGoldens, setAllGoldens] = useState([]);
  const [modalGoldenId, setModalGoldenId] = useState('');
  const [modalBusy, setModalBusy] = useState(false);
  const [modalMessage, setModalMessage] = useState('');

  const fallback = useMemo(() => {
    const golden = demoGoldenRecords.find((item) => item.golden_id === goldenId) || demoGoldenRecords[0];
    return {
      golden,
      sourceLinks: golden.source_links || [],
      provenance: golden.field_provenance || [],
      history: golden.history || [],
      audit: demoAuditEvents,
    };
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
    [goldenId, refreshKey],
  );

  const golden = data.golden?.golden_id ? data.golden : fallback.golden;
  const sourceLinks = extractArray(data.sourceLinks, ['items', 'records'], fallback.sourceLinks);

  // Field provenance: prefer field_values array from API response
  const rawProv = data.provenance;
  const provenanceRows = Array.isArray(rawProv?.field_values) && rawProv.field_values.length > 0
    ? rawProv.field_values.map((item) => ({
        field: item.field_name,
        chosen_value: item.field_value,
        winner_source: item.source_system_id || item.source_record_id || '—',
        rule: item.applied_rule_id || '—',
      }))
    : extractArray(rawProv, ['items', 'fields'], fallback.provenance);

  const history = extractArray(data.history, ['items', 'events'], fallback.history);
  const audit = extractArray(data.audit, ['items', 'events'], fallback.audit);

  // Load all golden records whenever a modal is opened
  useEffect(() => {
    if (modal) {
      setModalGoldenId('');
      setModalMessage('');
      api.getGoldenRecords({})
        .then((records) => setAllGoldens(Array.isArray(records) ? records : demoGoldenRecords))
        .catch(() => setAllGoldens(demoGoldenRecords));
    }
  }, [modal]);

  function openStewardAction(action) {
    setLinkMessage('');
    if (action === 'link') {
      setLinkMode('link');
      setLinkResults(null);
      setLinkSearch('');
      setTab('Linked Sources');
    } else if (action === 'unlink') {
      setLinkMode('unlink');
      setTab('Linked Sources');
    } else if (action === 'override') {
      setLinkMode('none');
      setTab('Field Provenance');
    } else if (action === 'duplicate') {
      setModal('duplicate');
    } else if (action === 'merge') {
      setModal('merge');
    }
  }

  async function handleLinkSearch() {
    setLinkBusy(true);
    setLinkMessage('');
    try {
      const result = await api.getSourceRecords(linkSearch ? { name: linkSearch } : {});
      setLinkResults(Array.isArray(result) ? result : result?.items || demoSourceRecords);
    } catch {
      const filtered = demoSourceRecords.filter(
        (s) => !linkSearch || s.name?.toLowerCase().includes(linkSearch.toLowerCase()),
      );
      setLinkResults(filtered);
    } finally {
      setLinkBusy(false);
    }
  }

  async function handleLinkSource(sourceRecordId) {
    setLinkBusy(true);
    setLinkMessage('');
    try {
      await api.linkSourceToGolden(goldenId, { source_record_id: sourceRecordId, actor: 'steward' });
      setLinkMessage(`✓ Linked ${sourceRecordId} to ${goldenId}.`);
      setLinkResults(null);
      setLinkSearch('');
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setLinkMessage(`Failed to link: ${err.message}`);
    } finally {
      setLinkBusy(false);
    }
  }

  async function handleUnlinkSource(sourceRecordId) {
    setLinkBusy(true);
    setLinkMessage('');
    try {
      await api.unlinkSourceFromGolden(goldenId, { source_record_id: sourceRecordId, reason: 'Manual unlink by steward', actor: 'steward' });
      setLinkMessage(`✓ Unlinked ${sourceRecordId} from ${goldenId}.`);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setLinkMessage(`Failed to unlink: ${err.message}`);
    } finally {
      setLinkBusy(false);
    }
  }

  async function handleModalAction(key, selectedId) {
    if (modal === 'duplicate') {
      if (key === 'pick_most_similar') {
        setModalBusy(true);
        try {
          const dups = await api.getDuplicates({});
          const list = Array.isArray(dups) ? dups : [];
          const related = list.filter((d) => d.golden_id_a === goldenId || d.golden_id_b === goldenId);
          if (related.length > 0) {
            const best = related.reduce((a, b) => (a.similarity_score >= b.similarity_score ? a : b));
            const otherId = best.golden_id_a === goldenId ? best.golden_id_b : best.golden_id_a;
            setModalGoldenId(otherId);
            setModalMessage(`Auto-selected ${otherId} (similarity score: ${Math.round(best.similarity_score * 100)}%).`);
          } else {
            setModalMessage('No existing similarity data found for this record. Please select a golden record manually.');
          }
        } catch {
          setModalMessage('Could not fetch similarity data. Please select manually.');
        } finally {
          setModalBusy(false);
        }
        return;
      }
      if (key === 'duplicate' && selectedId) {
        setModalBusy(true);
        try {
          await api.createDuplicate({ golden_id_a: goldenId, golden_id_b: selectedId, actor: 'steward' });
          setModalMessage(`✓ Duplicate pair (${goldenId} / ${selectedId}) added to the Duplicate Golden Queue.`);
        } catch (err) {
          setModalMessage(`Error: ${err.message}`);
        } finally {
          setModalBusy(false);
        }
      }
    } else if (modal === 'merge') {
      if (!selectedId) return;
      setModalBusy(true);
      try {
        if (key === 'merge_left_into_right') {
          await api.mergeGolden(goldenId, { target_golden_id: selectedId, merge_reason: 'Manual merge by steward', actor: 'steward' });
          setModalMessage(`✓ Merged ${goldenId} into ${selectedId}.`);
        } else if (key === 'merge_right_into_left') {
          await api.mergeGolden(selectedId, { target_golden_id: goldenId, merge_reason: 'Manual merge by steward', actor: 'steward' });
          setModalMessage(`✓ Merged ${selectedId} into ${goldenId}.`);
        }
        setRefreshKey((k) => k + 1);
      } catch (err) {
        setModalMessage(`Error: ${err.message}`);
      } finally {
        setModalBusy(false);
      }
    }
  }

  const duplicateActions = [
    { key: 'pick_most_similar', label: 'Choose Most Similar Golden Record', requiresSelection: false },
    { key: 'duplicate', label: 'Duplicate', primary: true, requiresSelection: true },
  ];
  const mergeActions = [
    { key: 'merge_left_into_right', label: 'Merge Left into Right', primary: true, requiresSelection: true },
    { key: 'merge_right_into_left', label: 'Merge Right into Left', primary: true, requiresSelection: true },
  ];

  return (
    <>
      {modal && (
        <GoldenPickModal
          title={modal === 'duplicate' ? 'Flag as Duplicate' : 'Merge with Another Golden'}
          currentGolden={golden}
          allGoldens={allGoldens}
          selectedId={modalGoldenId}
          onSelectId={setModalGoldenId}
          onClose={() => setModal(null)}
          onAction={handleModalAction}
          actionButtons={modal === 'duplicate' ? duplicateActions : mergeActions}
          busy={modalBusy}
          message={modalMessage}
        />
      )}
      <div className="page-stack">
        <div className="page-header">
          <div>
            <h2>{golden.canonical_name || golden.name}</h2>
            <p className="muted-text">Golden ID: {golden.golden_id}</p>
          </div>
        </div>
        <ApiStatusBanner error={error} />
        {loading && <div className="card subtle">Loading golden record…</div>}
        <div className="two-col">
          <div className="card">
            <h3>Canonical profile</h3>
            <div className="detail-grid">
              {Object.entries({
                Email: golden.canonical_email || golden.email,
                Phone: golden.canonical_phone || golden.phone,
                HKID: golden.canonical_hkid || golden.hkid,
                EmplId: golden.canonical_emplid || golden.emplid,
                StudentID: golden.canonical_studentid || golden.studentid,
                AlumniID: golden.canonical_alumniid || golden.alumniid,
                Address: golden.canonical_address || golden.address,
                Status: golden.status,
                'Person type': golden.person_type,
                'Last updated': formatDate(golden.last_updated || golden.updated_at),
              }).map(([label, value]) => (
                <div key={label}><strong>{label}:</strong> {value || '—'}</div>
              ))}
            </div>
          </div>
          <div className="card">
            <h3>Steward actions</h3>
            {role === 'Viewer' ? (
              <div className="empty-state">Viewer role can inspect but cannot change links or survivorship outcomes.</div>
            ) : (
              <div className="button-row wrap">
                <button type="button" className="button" onClick={() => openStewardAction('link')}>Link Source Record</button>
                <button type="button" className="button" onClick={() => openStewardAction('unlink')}>Unlink Source Record</button>
                <button type="button" className="button" onClick={() => openStewardAction('override')}>Apply Field Override</button>
                <button type="button" className="button" onClick={() => openStewardAction('duplicate')}>Flag as Duplicate</button>
                <button type="button" className="button" onClick={() => openStewardAction('merge')}>Merge with Another Golden</button>
              </div>
            )}
          </div>
        </div>
        <div className="tab-row">
          {tabs.map((item) => (
            <button key={item} className={`tab ${tab === item ? 'active' : ''}`} onClick={() => setTab(item)}>{item}</button>
          ))}
        </div>
        <div className="card">
          {tab === 'Overview' && (
            <div className="empty-state">Use the tabs to inspect provenance, history, and audit context for this profile.</div>
          )}

          {tab === 'Linked Sources' && (
            <>
              {/* Link new source record panel */}
              {linkMode === 'link' && (
                <div className="top-gap">
                  <h4>Link a new source record to {goldenId}</h4>
                  <div className="button-row">
                    <input
                      style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 'inherit' }}
                      value={linkSearch}
                      onChange={(e) => setLinkSearch(e.target.value)}
                      placeholder="Search by name (or leave blank for all)"
                      onKeyDown={(e) => e.key === 'Enter' && handleLinkSearch()}
                    />
                    <button type="button" className="button primary" onClick={handleLinkSearch} disabled={linkBusy}>
                      {linkBusy ? 'Searching…' : 'Search'}
                    </button>
                    <button type="button" className="button" onClick={() => { setLinkMode('none'); setLinkResults(null); setLinkMessage(''); }}>Cancel</button>
                  </div>
                  {linkResults !== null && (
                    <div className="table-wrap top-gap">
                      <table className="data-table">
                        <thead>
                          <tr><th>Source Record</th><th>Source System</th><th>Source PK</th><th>Status</th><th>Action</th></tr>
                        </thead>
                        <tbody>
                          {linkResults.map((row) => (
                            <tr key={row.source_record_id}>
                              <td>{row.source_record_id}</td>
                              <td>{row.source_system}</td>
                              <td>{row.source_pk}</td>
                              <td>{row.status}</td>
                              <td>
                                <button type="button" className="button primary" disabled={linkBusy} onClick={() => handleLinkSource(row.source_record_id)}>Link</button>
                              </td>
                            </tr>
                          ))}
                          {linkResults.length === 0 && (
                            <tr><td colSpan={5} className="empty-cell">No source records found.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Currently linked sources */}
              <div className={linkMode === 'link' ? 'top-gap' : ''}>
                <h4>Linked source records</h4>
                <div className="table-wrap">
                  <table className="data-table clickable-table">
                    <thead>
                      <tr>
                        <th>Source Record</th>
                        <th>Source System</th>
                        <th>Source PK</th>
                        <th>Status</th>
                        {linkMode === 'unlink' && <th>Action</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {sourceLinks.map((row) => (
                        <tr
                          key={row.source_record_id}
                          onClick={linkMode !== 'unlink' ? () => navigate(`/sources/${row.source_record_id}`) : undefined}
                          style={linkMode !== 'unlink' ? { cursor: 'pointer' } : undefined}
                        >
                          <td>{row.source_record_id}</td>
                          <td>{row.source_system || row.source_record?.source_system}</td>
                          <td>{row.source_pk || row.source_record?.source_pk}</td>
                          <td>{row.link_status || row.status}</td>
                          {linkMode === 'unlink' && (
                            <td>
                              <button
                                type="button"
                                className="button"
                                disabled={linkBusy}
                                onClick={(e) => { e.stopPropagation(); handleUnlinkSource(row.source_record_id); }}
                              >
                                Unlink
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {sourceLinks.length === 0 && (
                        <tr><td colSpan={linkMode === 'unlink' ? 5 : 4} className="empty-cell">No linked source records.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
                {linkMode === 'unlink' && (
                  <div className="button-row top-gap">
                    <button type="button" className="button" onClick={() => { setLinkMode('none'); setLinkMessage(''); }}>Done</button>
                  </div>
                )}
                {linkMessage && <div className="muted-text top-gap">{linkMessage}</div>}
              </div>
            </>
          )}

          {tab === 'Field Provenance' && (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr><th>Field</th><th>Chosen Value</th><th>Winner Source</th><th>Rule</th></tr>
                </thead>
                <tbody>
                  {provenanceRows.map((row, index) => (
                    <tr key={`${row.field}-${index}`}>
                      <td>{row.field}</td>
                      <td>{row.chosen_value || '—'}</td>
                      <td>{row.winner_source}</td>
                      <td>{row.rule}</td>
                    </tr>
                  ))}
                  {provenanceRows.length === 0 && (
                    <tr><td colSpan={4} className="empty-cell">No field provenance data available for this record.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Match History' && <AuditTimeline events={history} />}
          {tab === 'Merge History' && <AuditTimeline events={history.filter((item) => item.event_type?.includes('merge') || item.event_type?.includes('link'))} />}
          {tab === 'Audit Events' && <AuditTimeline events={audit} />}
        </div>
      </div>
    </>
  );
}
