const BASE_URL = import.meta.env.VITE_IRE_API_BASE_URL || 'http://localhost:8000';

async function apiCall(path, options = {}) {
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    if (err instanceof TypeError && err.message.includes('fetch')) {
      throw new Error('Backend unavailable. Running in demo mode.');
    }
    throw err;
  }
}

export const api = {
  health: () => apiCall('/health'),
  getDashboardSummary: () => apiCall('/ire/dashboard/summary'),
  getProcessCounts: () => apiCall('/ire/dashboard/process-counts'),
  getRecentActivity: () => apiCall('/ire/dashboard/recent-activity'),
  ingest: (data) => apiCall('/ire/ingest', { method: 'POST', body: JSON.stringify(data) }),
  ingestBatch: (data) => apiCall('/ire/ingest/batch', { method: 'POST', body: JSON.stringify(data) }),
  getBatches: () => apiCall('/ire/ingest/batches'),
  getBatch: (id) => apiCall(`/ire/ingest/batches/${id}`),
  getBatchRecords: (id) => apiCall(`/ire/ingest/batches/${id}/records`),
  getGoldenRecords: (params) => apiCall(`/ire/golden?${new URLSearchParams(params || {})}`),
  getGoldenRecord: (id) => apiCall(`/ire/golden/${id}`),
  createGoldenRecord: (data) => apiCall('/ire/golden', { method: 'POST', body: JSON.stringify(data) }),
  updateGoldenRecord: (id, data) => apiCall(`/ire/golden/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  linkSourceToGolden: (goldenId, data) => apiCall(`/ire/golden/${goldenId}/link-source`, { method: 'POST', body: JSON.stringify(data) }),
  unlinkSourceFromGolden: (goldenId, data) => apiCall(`/ire/golden/${goldenId}/unlink-source`, { method: 'POST', body: JSON.stringify(data) }),
  getGoldenSourceLinks: (id) => apiCall(`/ire/golden/${id}/source-links`),
  getGoldenHistory: (id) => apiCall(`/ire/golden/${id}/history`),
  getGoldenFieldProvenance: (id) => apiCall(`/ire/golden/${id}/field-provenance`),
  getSourceRecords: (params) => apiCall(`/ire/source-records?${new URLSearchParams(params || {})}`),
  getSourceRecord: (id) => apiCall(`/ire/source-records/${id}`),
  getSourceRecordNormalized: (id) => apiCall(`/ire/source-records/${id}/normalized`),
  getSourceRecordCandidates: (id) => apiCall(`/ire/source-records/${id}/candidates`),
  getSourceRecordHistory: (id) => apiCall(`/ire/source-records/${id}/history`),
  linkSourceRecord: (id, data) => apiCall(`/ire/source-records/${id}/link`, { method: 'POST', body: JSON.stringify(data) }),
  unlinkSourceRecord: (id, data) => apiCall(`/ire/source-records/${id}/unlink`, { method: 'POST', body: JSON.stringify(data) }),
  createGoldenFromSource: (id) => apiCall(`/ire/source-records/${id}/create-golden`, { method: 'POST', body: JSON.stringify({}) }),
  rematchSourceRecord: (id) => apiCall(`/ire/source-records/${id}/rematch`, { method: 'POST', body: JSON.stringify({}) }),
  getMatchCandidates: (params) => apiCall(`/ire/match-candidates?${new URLSearchParams(params || {})}`),
  getMatchCandidate: (id) => apiCall(`/ire/match-candidates/${id}`),
  getMatchCandidateFeatures: (id) => apiCall(`/ire/match-candidates/${id}/features`),
  getReviewTasks: (params) => apiCall(`/ire/review/tasks?${new URLSearchParams(params || {})}`),
  getReviewTask: (id) => apiCall(`/ire/review/tasks/${id}`),
  assignReviewTask: (id, data) => apiCall(`/ire/review/tasks/${id}/assign`, { method: 'POST', body: JSON.stringify(data) }),
  submitReviewDecision: (id, data) => apiCall(`/ire/review/tasks/${id}/decision`, { method: 'POST', body: JSON.stringify(data) }),
  getReviewTaskHistory: (id) => apiCall(`/ire/review/tasks/${id}/history`),
  getDuplicates: (params) => apiCall(`/ire/golden-duplicates?${new URLSearchParams(params || {})}`),
  getDuplicate: (id) => apiCall(`/ire/golden-duplicates/${id}`),
  submitDuplicateDecision: (id, data) => apiCall(`/ire/golden-duplicates/${id}/decision`, { method: 'POST', body: JSON.stringify(data) }),
  getMatchingFeatures: () => apiCall('/ire/matching-features'),
  updateMatchingFeature: (id, data) => apiCall(`/ire/matching-features/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getMatchingRules: () => apiCall('/ire/matching-rules'),
  createMatchingRule: (data) => apiCall('/ire/matching-rules', { method: 'POST', body: JSON.stringify(data) }),
  updateMatchingRule: (id, data) => apiCall(`/ire/matching-rules/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteMatchingRule: (id) => apiCall(`/ire/matching-rules/${id}`, { method: 'DELETE' }),
  getThresholds: () => apiCall('/ire/settings/thresholds'),
  updateThresholds: (data) => apiCall('/ire/settings/thresholds', { method: 'PUT', body: JSON.stringify(data) }),
  runSimulation: (data) => apiCall('/ire/rule-simulation', { method: 'POST', body: JSON.stringify(data) }),
  getSimulation: (id) => apiCall(`/ire/rule-simulation/${id}`),
  getSimulationResults: (id) => apiCall(`/ire/rule-simulation/${id}/results`),
  getSurvivorshipRules: () => apiCall('/ire/survivorship-rules'),
  createSurvivorshipRule: (data) => apiCall('/ire/survivorship-rules', { method: 'POST', body: JSON.stringify(data) }),
  updateSurvivorshipRule: (id, data) => apiCall(`/ire/survivorship-rules/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSurvivorshipRule: (id) => apiCall(`/ire/survivorship-rules/${id}`, { method: 'DELETE' }),
  survivorshipPreview: (data) => apiCall('/ire/survivorship/preview', { method: 'POST', body: JSON.stringify(data) }),
  getSourceSystems: () => apiCall('/ire/source-systems'),
  createSourceSystem: (data) => apiCall('/ire/source-systems', { method: 'POST', body: JSON.stringify(data) }),
  updateSourceSystem: (id, data) => apiCall(`/ire/source-systems/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSourceSystem: (id) => apiCall(`/ire/source-systems/${id}`, { method: 'DELETE' }),
  getAuditEvents: (params) => apiCall(`/ire/audit-events?${new URLSearchParams(params || {})}`),
  getAuditEvent: (id) => apiCall(`/ire/audit-events/${id}`),
};
