import { Link } from 'react-router-dom';
import { api } from '../api/client.js';
import ApiStatusBanner from '../components/ApiStatusBanner.jsx';
import ProcessStepper from '../components/ProcessStepper.jsx';
import { demoDashboard } from './demoData.js';
import { extractArray, extractObject, usePageData } from './pageHelpers.js';

const metricLabels = [
  ['total_source_records', 'Total source records'],
  ['total_golden_records', 'Total golden records'],
  ['auto_merged', 'Auto-merged'],
  ['manual_review_pending', 'Manual review pending'],
  ['new_golden_records', 'New golden records'],
  ['tier1_conflicts', 'Tier 1 conflicts'],
  ['duplicate_golden_alerts', 'Duplicate golden alerts'],
  ['failed_ingestion', 'Failed ingestion'],
];

export default function Dashboard() {
  const { loading, error, data } = usePageData(
    async () => {
      const [summary, counts, recentActivity] = await Promise.all([
        api.getDashboardSummary(),
        api.getProcessCounts(),
        api.getRecentActivity(),
      ]);
      return { summary, counts, recentActivity };
    },
    demoDashboard,
    []
  );

  const summary = extractObject(data.summary, ['summary'], demoDashboard.summary);
  const counts = extractObject(data.counts, ['counts'], demoDashboard.counts);
  const recentActivity = extractArray(data.recentActivity, ['events', 'items'], demoDashboard.recentActivity);

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p className="muted-text">Track the IRE pipeline from ingestion through merge decisions.</p>
        </div>
      </div>
      <ApiStatusBanner error={error} />
      {loading && <div className="card subtle">Loading dashboard…</div>}
      <div className="card">
        <h3>Pipeline overview</h3>
        <ProcessStepper currentStep="decision" counts={counts} />
      </div>
      <div className="metric-grid">
        {metricLabels.map(([key, label]) => (
          <div key={key} className="card metric-card">
            <div className="metric-value">{summary[key] ?? 0}</div>
            <div className="muted-text">{label}</div>
          </div>
        ))}
      </div>
      <div className="three-col">
        <div className="card">
          <h3>Quick actions</h3>
          <div className="button-row wrap">
            <Link className="button primary" to="/ingestion/new">New Case</Link>
            <Link className="button" to="/manual-review">View Manual Review Queue</Link>
            <Link className="button" to="/golden">Search Golden Records</Link>
          </div>
        </div>
        <div className="card span-2">
          <h3>Recent activity</h3>
          {recentActivity.length ? (
            <ul className="activity-list">
              {recentActivity.map((item, index) => (
                <li key={`${item.event_type}-${index}`}>
                  <strong>{item.event_type?.replace(/_/g, ' ')}</strong>
                  <div>{item.details}</div>
                  <div className="muted-text">{item.actor} · {item.event_ts}</div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">No recent activity available.</div>
          )}
        </div>
      </div>
    </div>
  );
}
