export default function AuditTimeline({ events = [] }) {
  if (!events.length) {
    return <div className="empty-state">No audit events available.</div>;
  }

  return (
    <div className="timeline">
      {events.map((event, index) => (
        <div key={`${event.event_type || 'event'}-${index}`} className="timeline-item">
          <div className="timeline-marker" />
          <div className="timeline-content card subtle">
            <div className="timeline-meta">
              <strong>{event.event_type?.replace(/_/g, ' ') || 'Activity'}</strong>
              <span>{event.event_ts || 'Unknown time'}</span>
            </div>
            <div className="muted-text">Actor: {event.actor || 'System'}</div>
            <div>{event.details || 'No extra details provided.'}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
