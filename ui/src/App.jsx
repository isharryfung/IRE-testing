import React, { useEffect, useMemo, useState } from 'react';
import {
  API_BASE_URL,
  getGolden,
  getHealth,
  getReviewTasks,
  getSourceRecord,
  postIngest,
  postMatch,
  postReviewDecision,
} from './api/client.js';
import ApiStatusBanner from './components/ApiStatusBanner.jsx';
import CandidateCard from './components/CandidateCard.jsx';
import DecisionBadge from './components/DecisionBadge.jsx';
import EvidenceTable from './components/EvidenceTable.jsx';
import RecordForm from './components/RecordForm.jsx';
import SafetyFlags from './components/SafetyFlags.jsx';
import demoTasks from './data/tasks.json';

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'ingest', label: 'Ingest Record' },
  { key: 'match', label: 'Match Record' },
  { key: 'review-queue', label: 'Manual Review Queue' },
  { key: 'golden', label: 'Golden Record View' },
];

const INITIAL_REVIEW_FORM = {
  reviewer: 'demo.reviewer',
  decision: 'accept_merge',
  goldenId: '',
  notes: '',
};

function parseRoute(hashValue) {
  const hash = (hashValue || '').replace(/^#\/?/, '');
  if (hash.startsWith('review-task/')) {
    return { page: 'review-task', taskId: hash.split('/')[1] };
  }
  const page = NAV_ITEMS.find((item) => item.key === hash)?.key;
  return { page: page || 'dashboard', taskId: null };
}

function goToPage(pageKey) {
  window.location.hash = `/${pageKey}`;
}

function goToReviewTask(taskId) {
  window.location.hash = `/review-task/${taskId}`;
}

function buildPayload(form) {
  return {
    name: form.name,
    email: form.email,
    phone: form.phone,
    address: form.address,
    hkid: form.hkid,
    emplid: form.emplid,
    studentid: form.studentid,
    alumniid: form.alumniid,
  };
}

function normalizeTask(task) {
  return {
    taskId: task.task_id,
    sourceRecordId: task.source_record_id || task.source_record?.record_id || null,
    sourceSystem: task.source_system || task.source_record?.source_system || task.source_record?.source_type || null,
    sourceRecord: task.source_record || null,
    reason: task.reason || '',
    confidence: task.best_confidence ?? task.confidence ?? 0,
    status: task.status || 'open',
    createdTs: task.created_ts || task.created_time || null,
    decisionHint: task.decision_hint || null,
    safetyFlags: task.safety_flags || [],
    evidence: task.features || task.evidence || [],
    candidateGoldenIds: task.candidate_golden_ids || [],
    candidates: task.candidates || (task.candidate ? [task.candidate] : []),
    raw: task,
  };
}

function renderKeyValue(data) {
  if (!data || typeof data !== 'object') {
    return <p className="muted">No data available.</p>;
  }
  return (
    <div className="table-wrap">
      <table className="table two-col-table">
        <tbody>
          {Object.entries(data).map(([key, value]) => (
            <tr key={key}>
              <th>{key}</th>
              <td>{typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '—')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [route, setRoute] = useState(parseRoute(window.location.hash));
  const [apiStatus, setApiStatus] = useState({ state: 'checking', baseUrl: API_BASE_URL, message: '' });
  const [demoMode, setDemoMode] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [taskError, setTaskError] = useState('');

  const [ingestResult, setIngestResult] = useState(null);
  const [ingestError, setIngestError] = useState('');
  const [matchResult, setMatchResult] = useState(null);
  const [matchError, setMatchError] = useState('');

  const [taskSourceRecord, setTaskSourceRecord] = useState(null);
  const [taskCandidates, setTaskCandidates] = useState([]);
  const [taskDetailNote, setTaskDetailNote] = useState('');
  const [reviewForm, setReviewForm] = useState(INITIAL_REVIEW_FORM);
  const [reviewMessage, setReviewMessage] = useState('');
  const [reviewError, setReviewError] = useState('');

  const [goldenLookupId, setGoldenLookupId] = useState('');
  const [goldenResult, setGoldenResult] = useState(null);
  const [goldenError, setGoldenError] = useState('');

  useEffect(() => {
    function onHashChange() {
      setRoute(parseRoute(window.location.hash));
    }

    window.addEventListener('hashchange', onHashChange);
    if (!window.location.hash) {
      goToPage('dashboard');
    }
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  async function loadTasks(isDemo) {
    if (isDemo) {
      setTasks(demoTasks.map(normalizeTask));
      setTaskError('');
      return;
    }

    try {
      const rows = await getReviewTasks('open');
      setTasks(Array.isArray(rows) ? rows.map(normalizeTask) : []);
      setTaskError('');
    } catch (error) {
      setTaskError(error.message);
      setTasks([]);
    }
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        const health = await getHealth();
        setApiStatus({ state: 'healthy', baseUrl: API_BASE_URL, message: health?.status || 'ok' });
        setDemoMode(false);
        await loadTasks(false);
      } catch (error) {
        setApiStatus({ state: 'unavailable', baseUrl: API_BASE_URL, message: error.message });
        setDemoMode(true);
        await loadTasks(true);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    async function loadTaskDetail() {
      setTaskSourceRecord(null);
      setTaskCandidates([]);
      setTaskDetailNote('');
      if (route.page !== 'review-task' || !route.taskId) {
        return;
      }
      const task = tasks.find((item) => item.taskId === route.taskId);
      if (!task) {
        setTaskDetailNote('Task not found in the current queue state.');
        return;
      }
      if (task.sourceRecord) {
        setTaskSourceRecord(task.sourceRecord);
      }

      if (demoMode) {
        setTaskSourceRecord(task.sourceRecord || null);
        setTaskCandidates(task.candidates || []);
        setTaskDetailNote('Demo mode: displaying local sample data because backend is unavailable.');
        return;
      }

      if (task.sourceRecordId && !task.sourceRecord) {
        try {
          const source = await getSourceRecord(task.sourceRecordId);
          setTaskSourceRecord(source);
        } catch {
          setTaskDetailNote('No review detail endpoint found. Showing list-level task data only.');
        }
      }

      if (task.candidateGoldenIds.length) {
        const candidates = await Promise.all(
          task.candidateGoldenIds.map(async (goldenId) => {
            try {
              return await getGolden(goldenId);
            } catch {
              return { golden_id: goldenId };
            }
          }),
        );
        setTaskCandidates(candidates);
      } else {
        setTaskCandidates(task.candidates || []);
      }

      if (!task.sourceRecord && !task.candidateGoldenIds.length) {
        setTaskDetailNote('No dedicated review detail endpoint. Available fields are from queue response.');
      }
    }

    loadTaskDetail();
  }, [route.page, route.taskId, tasks, demoMode]);

  const selectedTask = useMemo(
    () => (route.taskId ? tasks.find((item) => item.taskId === route.taskId) : null),
    [tasks, route.taskId],
  );

  const openTaskCount = tasks.filter((task) => task.status === 'open' || task.status === 'pending').length;

  async function handleIngestSubmit(form, resetForm) {
    setIngestError('');
    setIngestResult(null);
    const body = {
      source_system: form.sourceSystem,
      source_pk: form.sourcePk,
      data: buildPayload(form),
    };

    if (demoMode) {
      setIngestResult({
        decision: 'manual-review',
        confidence: 0.73,
        best_golden_id: 'GR-DEMO-001',
        reason: 'Demo response while API is offline.',
        safety_flags: ['backend_unavailable_demo_mode'],
        features: [
          {
            feature_name: 'email',
            feature_type: 'contact',
            source_value: body.data.email,
            golden_value: 'jsmith@ust.hk',
            similarity_algorithm: 'exact',
            similarity_score: 1,
            weight: 0.45,
            weighted_score: 0.45,
            is_conflict: false,
            is_blocking_feature: false,
          },
        ],
      });
      resetForm();
      return;
    }

    try {
      const result = await postIngest(body);
      setIngestResult(result);
      resetForm();
      await loadTasks(false);
    } catch (error) {
      setIngestError(error.message);
    }
  }

  async function handleMatchSubmit(form) {
    setMatchError('');
    setMatchResult(null);
    const body = {
      source_system: form.sourceSystem,
      data: buildPayload(form),
    };

    if (demoMode) {
      setMatchResult({
        decision: 'manual-review',
        confidence: 0.68,
        best_golden_id: 'GR-DEMO-002',
        reason: 'Demo match result while API is offline.',
        candidates: [{ golden_id: 'GR-DEMO-002', confidence: 0.68 }, { golden_id: 'GR-DEMO-010', confidence: 0.63 }],
        features: [
          {
            feature_name: 'name',
            feature_type: 'profile',
            source_value: body.data.name,
            golden_value: 'Jane Chan',
            similarity_algorithm: 'sequence_matcher',
            similarity_score: 0.74,
            weight: 0.25,
            weighted_score: 0.185,
            is_conflict: false,
            is_blocking_feature: false,
          },
        ],
      });
      return;
    }

    try {
      setMatchResult(await postMatch(body));
    } catch (error) {
      setMatchError(error.message);
    }
  }

  async function handleReviewDecisionSubmit(event) {
    event.preventDefault();
    setReviewMessage('');
    setReviewError('');
    if (!selectedTask) {
      return;
    }

    if (demoMode) {
      setReviewMessage(`Demo mode: ${reviewForm.decision} recorded for ${selectedTask.taskId}.`);
      setTasks((prev) => prev.map((task) => (task.taskId === selectedTask.taskId ? { ...task, status: 'resolved' } : task)));
      return;
    }

    try {
      await postReviewDecision(selectedTask.taskId, {
        reviewer: reviewForm.reviewer,
        decision: reviewForm.decision,
        golden_id: reviewForm.goldenId || null,
        notes: reviewForm.notes,
      });
      setReviewMessage(`Decision submitted for ${selectedTask.taskId}.`);
      await loadTasks(false);
    } catch (error) {
      setReviewError(error.message);
    }
  }

  async function handleGoldenLookup(event) {
    event.preventDefault();
    setGoldenError('');
    setGoldenResult(null);

    if (!goldenLookupId.trim()) {
      setGoldenError('Please enter a golden_id.');
      return;
    }

    if (demoMode) {
      const demoCandidate = demoTasks.flatMap((task) => [task.candidate]).find((candidate) => candidate?.record_id === goldenLookupId);
      if (demoCandidate) {
        setGoldenResult({
          golden_id: demoCandidate.record_id,
          canonical_name: demoCandidate.name,
          canonical_email: demoCandidate.email,
          canonical_phone: demoCandidate.phone,
          canonical_address: demoCandidate.address,
          linked_source_records: [demoTasks[0]?.source_record?.record_id].filter(Boolean),
        });
      } else {
        setGoldenError('Demo mode: golden record not found in sample data.');
      }
      return;
    }

    try {
      setGoldenResult(await getGolden(goldenLookupId.trim()));
    } catch (error) {
      setGoldenError(error.message);
    }
  }

  function renderDashboardPage() {
    return (
      <section className="stack">
        <h2>Dashboard</h2>
        <div className="grid cards">
          <div className="card">
            <h3>API Health</h3>
            <p>{apiStatus.state === 'healthy' ? 'Connected' : 'Unavailable'}</p>
          </div>
          <div className="card">
            <h3>Manual Review Tasks</h3>
            <p>{openTaskCount}</p>
          </div>
          <div className="card">
            <h3>Mode</h3>
            <p>{demoMode ? 'Demo mode (backend unreachable)' : 'Live API mode'}</p>
          </div>
        </div>
        <div className="card">
          <h3>Quick Links</h3>
          <div className="quick-links">
            <button onClick={() => goToPage('ingest')}>Ingest</button>
            <button onClick={() => goToPage('match')}>Match</button>
            <button onClick={() => goToPage('review-queue')}>Review Queue</button>
            <button onClick={() => goToPage('golden')}>Golden Lookup</button>
          </div>
        </div>
      </section>
    );
  }

  function renderDecisionResult(result) {
    if (!result) return null;

    return (
      <div className="card stack">
        <h3>Decision Result</h3>
        <p><strong>Decision:</strong> <DecisionBadge decision={result.decision} /></p>
        <p><strong>Best Candidate:</strong> {result.best_golden_id || '—'}</p>
        <p><strong>Confidence:</strong> {result.confidence ?? '—'}</p>
        <p><strong>Reason:</strong> {result.reason || '—'}</p>
        <SafetyFlags flags={result.safety_flags} />
        {Array.isArray(result.candidates) && result.candidates.length > 0 && (
          <>
            <h4>Candidates</h4>
            <div className="grid cards">
              {result.candidates.map((candidate, index) => (
                <CandidateCard key={candidate.golden_id || candidate.id || index} candidate={candidate} />
              ))}
            </div>
          </>
        )}
        <h4>Evidence</h4>
        <EvidenceTable evidence={result.features || result.evidence || []} />
      </div>
    );
  }

  function renderIngestPage() {
    return (
      <section className="stack">
        <h2>Ingest Record</h2>
        <RecordForm includeSourcePk submitLabel="Submit Ingest" onSubmit={handleIngestSubmit} />
        {ingestError && <p className="error">{ingestError}</p>}
        {renderDecisionResult(ingestResult)}
      </section>
    );
  }

  function renderMatchPage() {
    return (
      <section className="stack">
        <h2>Match Record</h2>
        <RecordForm includeSourcePk={false} submitLabel="Run Match" onSubmit={handleMatchSubmit} />
        {matchError && <p className="error">{matchError}</p>}
        {renderDecisionResult(matchResult)}
      </section>
    );
  }

  function renderReviewQueuePage() {
    if (!tasks.length) {
      return (
        <section className="stack">
          <h2>Manual Review Queue</h2>
          <p className="muted">{taskError || (demoMode ? 'No demo tasks available.' : 'No open review tasks at the moment.')}</p>
        </section>
      );
    }

    return (
      <section className="stack">
        <h2>Manual Review Queue</h2>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Task ID</th>
                <th>Source System</th>
                <th>Source Record</th>
                <th>Reason</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.taskId}>
                  <td><button className="link-button" onClick={() => goToReviewTask(task.taskId)}>{task.taskId}</button></td>
                  <td>{task.sourceSystem || '—'}</td>
                  <td>{task.sourceRecordId || '—'}</td>
                  <td>{task.reason || '—'}</td>
                  <td>{task.confidence ?? '—'}</td>
                  <td>{task.status}</td>
                  <td>{task.createdTs || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  function renderReviewTaskPage() {
    if (!selectedTask) {
      return (
        <section className="stack">
          <h2>Review Task Detail</h2>
          <p className="muted">Task not found. Open a task from the queue.</p>
        </section>
      );
    }

    return (
      <section className="stack">
        <h2>Review Task Detail</h2>
        <p><strong>Task:</strong> {selectedTask.taskId}</p>
        <p><strong>Reason:</strong> {selectedTask.reason || '—'}</p>
        <p><strong>Decision Hint:</strong> <DecisionBadge decision={selectedTask.decisionHint || 'manual-review'} /></p>
        <p><strong>Confidence:</strong> {selectedTask.confidence ?? '—'}</p>
        <SafetyFlags flags={selectedTask.safetyFlags} />
        {taskDetailNote && <p className="muted">{taskDetailNote}</p>}

        <div className="card">
          <h3>Incoming Record</h3>
          {renderKeyValue(taskSourceRecord || selectedTask.sourceRecord || { source_record_id: selectedTask.sourceRecordId })}
        </div>

        <div className="card stack">
          <h3>Candidate Golden Records</h3>
          {taskCandidates.length ? (
            <div className="grid cards">
              {taskCandidates.map((candidate, index) => (
                <CandidateCard key={candidate.golden_id || index} candidate={candidate} />
              ))}
            </div>
          ) : (
            <p className="muted">No detailed candidate payload available from current backend response.</p>
          )}
        </div>

        <div className="card stack">
          <h3>Feature Evidence</h3>
          <EvidenceTable evidence={selectedTask.evidence} />
        </div>

        <form onSubmit={handleReviewDecisionSubmit} className="card stack">
          <h3>Reviewer Decision</h3>
          <div className="grid two-col">
            <label>Reviewer<input value={reviewForm.reviewer} onChange={(event) => setReviewForm((prev) => ({ ...prev, reviewer: event.target.value }))} required /></label>
            <label>Decision
              <select value={reviewForm.decision} onChange={(event) => setReviewForm((prev) => ({ ...prev, decision: event.target.value }))}>
                <option value="accept_merge">accept_merge</option>
                <option value="reject_candidate">reject_candidate</option>
                <option value="create_new_golden">create_new_golden</option>
                <option value="escalate">escalate</option>
              </select>
            </label>
            <label>Selected Golden ID (optional)<input value={reviewForm.goldenId} onChange={(event) => setReviewForm((prev) => ({ ...prev, goldenId: event.target.value }))} /></label>
            <label>Notes<textarea value={reviewForm.notes} onChange={(event) => setReviewForm((prev) => ({ ...prev, notes: event.target.value }))} /></label>
          </div>
          <button type="submit">Submit Review Decision</button>
          {reviewMessage && <p className="success">{reviewMessage}</p>}
          {reviewError && <p className="error">{reviewError}</p>}
        </form>
      </section>
    );
  }

  function renderGoldenPage() {
    const linkedSourceRecords = goldenResult?.linked_source_records || goldenResult?.source_records || goldenResult?.record_links;
    const mergeHistory = goldenResult?.merge_history || goldenResult?.history || goldenResult?.audit_history;
    const provenance = goldenResult?.provenance;

    const canonical = goldenResult
      ? {
          golden_id: goldenResult.golden_id,
          canonical_name: goldenResult.canonical_name,
          canonical_email: goldenResult.canonical_email,
          canonical_phone: goldenResult.canonical_phone,
          canonical_hkid: goldenResult.canonical_hkid,
          canonical_emplid: goldenResult.canonical_emplid,
          canonical_studentid: goldenResult.canonical_studentid,
          canonical_alumniid: goldenResult.canonical_alumniid,
          canonical_address: goldenResult.canonical_address,
          person_type: goldenResult.person_type,
          status: goldenResult.status,
          last_updated: goldenResult.last_updated,
        }
      : null;

    return (
      <section className="stack">
        <h2>Golden Record View</h2>
        <form onSubmit={handleGoldenLookup} className="inline-form">
          <input
            placeholder="Enter golden_id"
            value={goldenLookupId}
            onChange={(event) => setGoldenLookupId(event.target.value)}
          />
          <button type="submit">Lookup</button>
        </form>
        {goldenError && <p className="error">{goldenError}</p>}

        {goldenResult && (
          <div className="stack">
            <div className="card">
              <h3>Canonical Fields</h3>
              {renderKeyValue(canonical)}
            </div>

            <div className="card">
              <h3>Linked Source Records</h3>
              {Array.isArray(linkedSourceRecords) ? renderKeyValue({ records: linkedSourceRecords }) : renderKeyValue(linkedSourceRecords)}
            </div>

            <div className="card">
              <h3>Field Provenance</h3>
              {renderKeyValue(provenance)}
            </div>

            <div className="card">
              <h3>Merge / Audit History</h3>
              {Array.isArray(mergeHistory) ? renderKeyValue({ events: mergeHistory }) : renderKeyValue(mergeHistory)}
            </div>
          </div>
        )}
      </section>
    );
  }

  function renderPage() {
    if (route.page === 'dashboard') return renderDashboardPage();
    if (route.page === 'ingest') return renderIngestPage();
    if (route.page === 'match') return renderMatchPage();
    if (route.page === 'review-queue') return renderReviewQueuePage();
    if (route.page === 'review-task') return renderReviewTaskPage();
    if (route.page === 'golden') return renderGoldenPage();
    return renderDashboardPage();
  }

  return (
    <main className="app-shell">
      <header className="stack">
        <h1>Identity Resolution Engine Frontend</h1>
        <ApiStatusBanner apiStatus={apiStatus} demoMode={demoMode} />
        <nav className="nav-row">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => goToPage(item.key)}
              className={route.page === item.key ? 'active' : ''}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      {renderPage()}
    </main>
  );
}
