import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import AuditTimeline from '../components/AuditTimeline.jsx';
import DecisionBadge from '../components/DecisionBadge.jsx';
import EvidenceTable from '../components/EvidenceTable.jsx';
import SafetyFlags from '../components/SafetyFlags.jsx';
import { demoReviewTasks } from './demoData.js';
import { extractArray, usePageData } from './pageHelpers.js';

export default function ManualReviewDetail() {
  const { taskId } = useParams();
  const fallback = useMemo(() => demoReviewTasks.find((item) => item.task_id === taskId) || demoReviewTasks[0], [taskId]);
  const [form, setForm] = useState({ reviewer: '', decision: 'accept_merge', notes: '', selected_golden_id: fallback.candidate?.record_id || '' });
  const [submitMessage, setSubmitMessage] = useState('');
  const { loading, error, data } = usePageData(
    async () => {
      const [task, history] = await Promise.all([api.getReviewTask(taskId), api.getReviewTaskHistory(taskId)]);
      return { task, history };
    },
    { task: fallback, history: fallback.history },
    [taskId]
  );
  const task = data.task?.task_id ? data.task : fallback;
  const history = extractArray(data.history, ['items', 'events'], fallback.history);
  const bestCandidate = task.candidates?.[0] || { features: [] };

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await api.submitReviewDecision(task.task_id, form);
      setSubmitMessage('Decision submitted to backend.');
    } catch {
      setSubmitMessage('Backend unavailable. Decision captured locally for demo walkthrough.');
    }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h2>Manual Review Task {task.task_id}</h2><p className="muted-text">Review the incoming source record against the best candidate golden profiles.</p></div></div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading review task…</div>}
      <div className="two-col">
        <div className="card">
          <h3>Incoming source record</h3>
          <pre className="code-block">{JSON.stringify(task.source_record, null, 2)}</pre>
          <div className="top-gap"><strong>Recommended decision:</strong> <DecisionBadge decision={task.recommended_decision} /></div>
          <div className="top-gap"><strong>Safety flags:</strong> <SafetyFlags flags={task.safety_flags || []} /></div>
        </div>
        <div className="card">
          <h3>Candidate Golden Records</h3>
          <div className="table-wrap"><table className="data-table"><thead><tr><th>Golden ID</th><th>Name</th><th>Score</th><th>Decision</th></tr></thead><tbody>{(task.candidates || []).map((candidate) => <tr key={candidate.golden_id}><td>{candidate.golden_id}</td><td>{candidate.golden_record?.canonical_name ?? candidate.name}</td><td>{Math.round(((candidate.total_score ?? candidate.score) || 0) * 100)}%</td><td><DecisionBadge decision={candidate.decision_hint ?? candidate.decision} /></td></tr>)}</tbody></table></div>
        </div>
      </div>
      <div className="card"><h3>Evidence for best candidate</h3><EvidenceTable features={bestCandidate.features || []} /></div>
      <div className="two-col">
        <form className="card form-grid" onSubmit={handleSubmit}>
          <h3>Decision form</h3>
          <label className="field"><span>Reviewer</span><input value={form.reviewer} onChange={(event) => setForm({ ...form, reviewer: event.target.value })} placeholder="Your name or ID" required /></label>
          <label className="field"><span>Action</span><select value={form.decision} onChange={(event) => setForm({ ...form, decision: event.target.value })}><option value="accept_merge">Accept Merge</option><option value="reject_candidate">Reject Candidate</option><option value="create_new_golden">Create New Golden</option><option value="escalate">Escalate</option><option value="request_more_info">Request More Info</option></select></label>
          <label className="field"><span>Golden ID (if applicable)</span><input value={form.selected_golden_id} onChange={(event) => setForm({ ...form, selected_golden_id: event.target.value })} /></label>
          <label className="field full-width"><span>Notes</span><textarea rows="5" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
          <div className="button-row"><button type="submit" className="button primary">Submit Decision</button></div>
          {submitMessage && <div className="muted-text">{submitMessage}</div>}
        </form>
        <div className="card">
          <h3>Previous decisions / history</h3>
          <AuditTimeline events={history} />
        </div>
      </div>
    </div>
  );
}
