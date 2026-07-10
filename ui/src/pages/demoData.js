import reviewSeed from '../data/tasks.json';
import { buildEvidence } from './pageHelpers.js';

export const demoSourceSystems = [
  { id: 'sis', name: 'Student Information System', trust_level: 'High', internal_external: 'Internal', auto_merge_allowed: true, status: 'Active' },
  { id: 'hr', name: 'HRMS', trust_level: 'High', internal_external: 'Internal', auto_merge_allowed: true, status: 'Active' },
  { id: 'alumni', name: 'Alumni CRM', trust_level: 'Medium', internal_external: 'External', auto_merge_allowed: false, status: 'Active' },
];

export const demoDashboard = {
  summary: {
    total_source_records: 1284,
    total_golden_records: 712,
    auto_merged: 945,
    manual_review_pending: 14,
    new_golden_records: 67,
    tier1_conflicts: 3,
    duplicate_golden_alerts: 6,
    failed_ingestion: 2,
  },
  counts: {
    ingested: 1284,
    normalized: 1279,
    matched: 1204,
    decision: 1204,
    auto_merged: 945,
    manual_review: 92,
    new_golden: 67,
  },
  recentActivity: [
    { event_type: 'manual_review_created', actor: 'IRE Engine', event_ts: '2025-04-10T09:10:00Z', details: 'TASK-001 created because score gap between top two candidates was below threshold.' },
    { event_type: 'auto_merge_applied', actor: 'System', event_ts: '2025-04-10T09:20:00Z', details: 'Source IN-003 automatically linked to GR-003.' },
    { event_type: 'duplicate_detected', actor: 'Duplicate detector', event_ts: '2025-04-10T09:35:00Z', details: 'Potential duplicate detected between GR-003 and GR-010.' },
  ],
};

export const demoGoldenRecords = [
  {
    golden_id: 'GR-001',
    name: 'John Michael Smith',
    email: 'jsmith@ust.hk',
    phone: '+8525551234567',
    hkid: 'A123456(7)',
    emplid: 'E1001',
    person_type: 'Staff',
    status: 'Active',
    linked_sources: 3,
    last_updated: '2025-04-10T08:45:00Z',
    address: 'Clear Water Bay',
    alumniid: '',
    studentid: '',
    possible_duplicate: false,
    source_links: [
      { source_record_id: 'IN-001', source_system: 'HRMS', source_pk: 'EMP-1001', link_status: 'Linked' },
      { source_record_id: 'IN-011', source_system: 'Access Card', source_pk: 'CARD-2001', link_status: 'Linked' },
    ],
    field_provenance: [
      { field: 'email', chosen_value: 'jsmith@ust.hk', winner_source: 'HRMS', rule: 'Most trusted source' },
      { field: 'phone', chosen_value: '+8525551234567', winner_source: 'Access Card', rule: 'Latest verified value' },
    ],
    history: [
      { event_type: 'golden_created', actor: 'System', event_ts: '2025-04-01T09:00:00Z', details: 'Golden record created from HRMS feed.' },
      { event_type: 'source_linked', actor: 'System', event_ts: '2025-04-10T08:45:00Z', details: 'IN-001 linked after match approval.' },
    ],
  },
  {
    golden_id: 'GR-002',
    name: 'Jane Chan',
    email: 'jchan@example.com',
    phone: '+85291234567',
    hkid: '',
    emplid: 'E2002',
    person_type: 'Staff',
    status: 'Active',
    linked_sources: 2,
    last_updated: '2025-04-10T09:12:00Z',
    address: 'Kowloon Tong',
    alumniid: 'AL-882',
    studentid: '',
    possible_duplicate: false,
    source_links: [
      { source_record_id: 'IN-005', source_system: 'Alumni CRM', source_pk: 'AL-882', link_status: 'Pending review' },
    ],
    field_provenance: [
      { field: 'address', chosen_value: 'Kowloon Tong', winner_source: 'HRMS', rule: 'Highest priority source' },
    ],
    history: [
      { event_type: 'field_override_applied', actor: 'Data Steward', event_ts: '2025-04-08T15:12:00Z', details: 'Email verified against alumni source.' },
    ],
  },
  {
    golden_id: 'GR-003',
    name: 'Alex Wong',
    email: 'alex.wong@ust.hk',
    phone: '+85298765432',
    hkid: '',
    emplid: '',
    person_type: 'Student',
    status: 'Active',
    linked_sources: 4,
    last_updated: '2025-04-10T09:20:00Z',
    address: 'Sai Kung',
    alumniid: '',
    studentid: 'S3003',
    possible_duplicate: true,
    source_links: [
      { source_record_id: 'IN-003', source_system: 'SIS', source_pk: 'S3003', link_status: 'Linked' },
    ],
    field_provenance: [
      { field: 'studentid', chosen_value: 'S3003', winner_source: 'SIS', rule: 'Exact identifier match' },
    ],
    history: [
      { event_type: 'auto_merge_applied', actor: 'System', event_ts: '2025-04-10T09:20:00Z', details: 'Source IN-003 automatically merged.' },
    ],
  },
  {
    golden_id: 'GR-010',
    name: 'Alexander Wong',
    email: 'a.wong@ust.hk',
    phone: '+85298765432',
    hkid: '',
    emplid: '',
    person_type: 'Student',
    status: 'Review',
    linked_sources: 1,
    last_updated: '2025-04-09T17:12:00Z',
    address: 'Sai Kung',
    alumniid: '',
    studentid: 'S3003X',
    possible_duplicate: true,
    source_links: [
      { source_record_id: 'IN-104', source_system: 'Events App', source_pk: 'EVT-9981', link_status: 'Linked' },
    ],
    field_provenance: [],
    history: [
      { event_type: 'duplicate_candidate_created', actor: 'System', event_ts: '2025-04-09T17:12:00Z', details: 'Pair submitted for duplicate review.' },
    ],
  },
];

export const demoSourceRecords = [
  {
    source_record_id: 'IN-001',
    source_system: 'HRMS',
    source_pk: 'EMP-1001',
    name: 'John Smith',
    email: 'jsmith@ust.hk',
    phone: '+852-555-123-4567',
    address: 'Clear Water Bay',
    status: 'Manual review',
    linked_golden: 'GR-001',
    created_at: '2025-04-10T08:42:00Z',
    hkid: '',
    normalized: { name: 'john smith', email: 'jsmith@ust.hk', phone: '+8525551234567', address: 'clear water bay', source_system: 'HRMS' },
    raw_payload: '{"name":"John Smith","email":"jsmith@ust.hk","phone":"+852-555-123-4567"}',
  },
  {
    source_record_id: 'IN-005',
    source_system: 'Alumni CRM',
    source_pk: 'AL-882',
    name: 'Jane C.',
    email: 'jchan@alumni.example.com',
    phone: '+85291234567',
    address: 'Kowloon Tong',
    status: 'Manual review',
    linked_golden: 'GR-002',
    created_at: '2025-04-10T08:55:00Z',
    hkid: '',
    normalized: { name: 'jane c', email: 'jchan@alumni.example.com', phone: '+85291234567', address: 'kowloon tong', source_system: 'Alumni CRM' },
    raw_payload: '{"name":"Jane C.","email":"jchan@alumni.example.com","phone":"+85291234567"}',
  },
  {
    source_record_id: 'IN-003',
    source_system: 'SIS',
    source_pk: 'S3003',
    name: 'A Wong',
    email: 'alex.wong@ust.hk',
    phone: '98765432',
    address: 'Sai Kung',
    status: 'Auto merged',
    linked_golden: 'GR-003',
    created_at: '2025-04-10T09:20:00Z',
    hkid: '',
    normalized: { name: 'a wong', email: 'alex.wong@ust.hk', phone: '+85298765432', address: 'sai kung', source_system: 'SIS' },
    raw_payload: '{"name":"A Wong","email":"alex.wong@ust.hk","phone":"98765432"}',
  },
];

const reasonCodes = ['tier1_conflict', 'multiple_candidates', 'low_confidence'];
const priorities = ['High', 'Medium', 'Low'];

export const demoReviewTasks = reviewSeed.map((task, index) => ({
  ...task,
  reason_code: reasonCodes[index] || 'low_confidence',
  priority: priorities[index] || 'Medium',
  assigned_to: index === 0 ? 'amy.chan' : index === 1 ? 'sam.lee' : 'system',
  created_at: `2025-04-10T0${index + 8}:15:00Z`,
  safety_flags: index === 0 ? ['multiple_high_candidates', 'low_score_gap'] : index === 1 ? ['untrusted_source'] : [],
  recommended_decision: index === 0 ? 'manual-review' : index === 1 ? 'create_new_golden' : 'auto-merge',
  candidates: [
    {
      golden_id: task.candidate.record_id,
      name: task.candidate.name,
      score: task.confidence,
      decision: task.confidence > 0.85 ? 'auto-merge' : 'manual-review',
      features: buildEvidence(task.source_record, task.candidate, task.similarities),
    },
    {
      golden_id: index === 0 ? 'GR-010' : 'GR-999',
      name: index === 0 ? 'Jon Smith' : 'Jane Choi',
      score: Math.max(task.confidence - 0.07, 0.32),
      decision: 'manual-review',
      features: buildEvidence(task.source_record, task.candidate, task.similarities),
    },
  ],
  history: [
    { event_type: 'task_created', actor: 'IRE Engine', event_ts: `2025-04-10T0${index + 8}:15:00Z`, details: task.reason },
    { event_type: 'task_assigned', actor: 'Queue manager', event_ts: `2025-04-10T0${index + 8}:17:00Z`, details: `Assigned to ${index === 0 ? 'amy.chan' : 'sam.lee'}` },
  ],
}));

export const demoMatchCandidates = demoReviewTasks.flatMap((task, index) =>
  task.candidates.map((candidate, candidateIndex) => ({
    candidate_id: `MC-${index + 1}${candidateIndex + 1}`,
    source_record: task.source_record,
    golden_record: demoGoldenRecords.find((item) => item.golden_id === candidate.golden_id) || { golden_id: candidate.golden_id, name: candidate.name },
    total_score: candidate.score,
    decision: candidate.decision,
    safety_flags: task.safety_flags,
    features: candidate.features,
  }))
);

export const demoDuplicates = [
  {
    duplicate_id: 'DUP-001',
    golden_a: demoGoldenRecords[2],
    golden_b: demoGoldenRecords[3],
    similarity_score: 0.91,
    status: 'Open',
    detection_method: 'Rule + ML hybrid',
    created_at: '2025-04-10T09:35:00Z',
    warnings: ['Same phone number', 'Student identifiers conflict'],
  },
];

export const demoMatchingFeatures = [
  { id: 'name', feature: 'name', display_label: 'Full name', enabled: true, priority: 1, algorithm: 'Jaro-Winkler', auto_merge_eligible: true, blocking: false, visible_in_review: true },
  { id: 'email', feature: 'email', display_label: 'Email address', enabled: true, priority: 2, algorithm: 'Exact', auto_merge_eligible: true, blocking: true, visible_in_review: true },
  { id: 'phone', feature: 'phone', display_label: 'Phone number', enabled: true, priority: 3, algorithm: 'Normalized exact', auto_merge_eligible: true, blocking: false, visible_in_review: true },
  { id: 'hkid', feature: 'hkid', display_label: 'HKID', enabled: true, priority: 4, algorithm: 'Exact', auto_merge_eligible: true, blocking: true, visible_in_review: true },
];

export const demoMatchingRules = [
  { id: 'RULE-001', name: 'Trusted identifiers first', type: 'Deterministic', active: true, version: 4, created: '2025-03-28T11:20:00Z', description: 'Auto-merge when trusted identifiers are exact and no conflict flags exist.' },
  { id: 'RULE-002', name: 'Human review for low score gap', type: 'Safety', active: true, version: 2, created: '2025-04-02T16:05:00Z', description: 'Route to reviewer when top two candidates are too close.' },
];

export const demoThresholds = {
  auto_merge_threshold: 0.85,
  manual_review_threshold: 0.5,
  multi_match_gap_threshold: 0.1,
};

export const demoSimulation = {
  simulation_id: 'SIM-001',
  results: [
    { source_record_id: 'IN-001', old_decision: 'manual-review', new_decision: 'auto-merge', note: 'Email weight increase improved confidence to 87%.' },
    { source_record_id: 'IN-005', old_decision: 'manual-review', new_decision: 'manual-review', note: 'No change because source remains untrusted.' },
  ],
};

export const demoSurvivorshipRules = [
  { id: 'SURV-001', name: 'Trusted contact details', active: true, version: 3, description: 'Prefer HRMS email and verified mobile for staff profiles.' },
  { id: 'SURV-002', name: 'Student identity preservation', active: true, version: 1, description: 'Prefer SIS student identifiers for student profiles.' },
];

export const demoAuditEvents = [
  { event_type: 'ingest_received', actor: 'API Gateway', event_ts: '2025-04-10T08:40:00Z', details: 'Received source record IN-001 from HRMS.' },
  { event_type: 'match_scored', actor: 'Matching Engine', event_ts: '2025-04-10T08:41:00Z', details: 'Compared IN-001 against 42 candidate golden records.' },
  { event_type: 'manual_review_created', actor: 'Matching Engine', event_ts: '2025-04-10T08:42:00Z', details: 'Created review task TASK-001 for steward verification.' },
];
