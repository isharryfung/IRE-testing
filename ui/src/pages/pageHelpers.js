import { useEffect, useState } from 'react';

export function getErrorMessage(error) {
  return error instanceof Error ? error.message : String(error || 'Unknown error');
}

export function usePageData(loader, demoData, deps = []) {
  const [state, setState] = useState({ loading: true, error: null, data: demoData });

  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: null }));
    Promise.resolve()
      .then(() => loader())
      .then((data) => {
        if (active) {
          setState({ loading: false, error: null, data: data ?? demoData });
        }
      })
      .catch((error) => {
        if (active) {
          setState({ loading: false, error: getErrorMessage(error), data: demoData });
        }
      });
    return () => {
      active = false;
    };
  }, deps);

  return state;
}

export function extractArray(data, keys = [], fallback = []) {
  if (Array.isArray(data)) return data;
  for (const key of keys) {
    if (Array.isArray(data?.[key])) {
      return data[key];
    }
  }
  return fallback;
}

export function extractObject(data, keys = [], fallback = {}) {
  for (const key of keys) {
    const value = data?.[key];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value;
    }
  }
  return data && typeof data === 'object' && !Array.isArray(data) ? data : fallback;
}

export function formatDate(value) {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

export function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return `${Math.round(Number(value) * 100)}%`;
}

export function buildEvidence(source = {}, golden = {}, similarities = {}) {
  return [
    ['Name', 'name', 'name', 'name_similarity', 1, 0.28],
    ['Email', 'email', 'email', 'email_exact', 1, 0.24],
    ['Phone', 'phone', 'phone', 'phone_normalized', 2, 0.18],
    ['HKID', 'hkid', 'hkid', 'id_exact', 3, 0.16],
    ['EmplId', 'emplid', 'emplid', 'id_exact', 4, 0.08],
    ['Student ID', 'studentid', 'studentid', 'id_exact', 5, 0.04],
    ['Address', 'address', 'address', 'address_similarity', 6, 0.02],
  ].map(([feature, leftKey, rightKey, algorithm, priority, weight]) => {
    const similarity = similarities[leftKey] ?? similarities[rightKey] ?? null;
    const flags = similarity === 0 ? ['conflict'] : [];
    return {
      feature,
      source_value: source[leftKey] || '—',
      golden_value: golden[rightKey] || '—',
      algorithm,
      similarity,
      priority,
      weight,
      weighted_score: similarity == null ? null : similarity * weight,
      flags,
    };
  });
}

export function formatDetails(details) {
  if (!details) return '';
  if (typeof details === 'string') return details;
  if (typeof details === 'object' && !Array.isArray(details)) {
    const values = Object.values(details).filter(Boolean);
    return values.join(' · ') || JSON.stringify(details);
  }
  return String(details);
}

export function describeStrength(score) {
  const numeric = Number(score || 0);
  if (numeric > 0.85) return 'Strong match';
  if (numeric >= 0.5) return 'Possible match';
  return 'Weak match';
}
