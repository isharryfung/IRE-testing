const API_BASE_URL = import.meta.env.VITE_IRE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(message, status = null, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function toJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    });
    const payload = await toJson(response);
    if (!response.ok) {
      const detail = payload?.detail || payload?.message || response.statusText;
      throw new ApiError(`API request failed: ${detail}`, response.status, payload);
    }
    return payload;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Unable to reach IRE API. Using demo mode if available.', null, error?.message || null);
  }
}

export function getHealth() {
  return request('/health');
}

export function postIngest(body) {
  return request('/ire/ingest', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function postMatch(body) {
  return request('/ire/match', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getGolden(goldenId) {
  return request(`/ire/golden/${encodeURIComponent(goldenId)}`);
}

export function getReviewTasks(status = 'open') {
  return request(`/ire/review/tasks?status=${encodeURIComponent(status)}`);
}

export function postReviewDecision(taskId, body) {
  return request(`/ire/review/${encodeURIComponent(taskId)}/decision`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getSourceRecord(sourceRecordId) {
  return request(`/ire/source/${encodeURIComponent(sourceRecordId)}`);
}

export { API_BASE_URL };
