import React from 'react';

export default function ApiStatusBanner({ apiStatus, demoMode }) {
  if (!apiStatus) {
    return null;
  }

  const isHealthy = apiStatus.state === 'healthy';
  const message = isHealthy
    ? `API connected (${apiStatus.baseUrl})`
    : demoMode
      ? 'Backend unavailable. Running in demo mode with sample data.'
      : apiStatus.message || 'API unavailable';

  return (
    <div className={`status-banner ${isHealthy ? 'status-ok' : 'status-warn'}`}>
      <strong>{isHealthy ? '✅' : '⚠️'} {message}</strong>
    </div>
  );
}
