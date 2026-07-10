CREATE TABLE source_systems (
    system_id VARCHAR2(50) PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    trust_level VARCHAR2(30) NOT NULL,
    is_internal CHAR(1) DEFAULT 'N' CHECK (is_internal IN ('Y', 'N')),
    auto_merge_allowed CHAR(1) DEFAULT 'Y' CHECK (auto_merge_allowed IN ('Y', 'N')),
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ingestion_batches (
    batch_id VARCHAR2(50) PRIMARY KEY,
    source_system_id VARCHAR2(50) NOT NULL REFERENCES source_systems(system_id),
    batch_status VARCHAR2(30) NOT NULL,
    total_records NUMBER DEFAULT 0,
    processed_records NUMBER DEFAULT 0,
    failed_records NUMBER DEFAULT 0,
    auto_merged NUMBER DEFAULT 0,
    manual_review_count NUMBER DEFAULT 0,
    new_golden_count NUMBER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR2(100)
);
CREATE INDEX idx_ingestion_batches_status ON ingestion_batches(batch_status);
CREATE INDEX idx_ingestion_batches_source ON ingestion_batches(source_system_id);

CREATE TABLE source_records (
    source_record_id VARCHAR2(50) PRIMARY KEY,
    source_system_id VARCHAR2(50) NOT NULL REFERENCES source_systems(system_id),
    ingestion_batch_id VARCHAR2(50) REFERENCES ingestion_batches(batch_id),
    source_pk VARCHAR2(150) NOT NULL,
    raw_name VARCHAR2(255),
    raw_email VARCHAR2(255),
    raw_phone VARCHAR2(80),
    raw_address VARCHAR2(500),
    raw_hkid VARCHAR2(80),
    raw_emplid VARCHAR2(80),
    raw_studentid VARCHAR2(80),
    raw_alumniid VARCHAR2(80),
    raw_payload CLOB,
    ingestion_status VARCHAR2(30) NOT NULL,
    validation_warnings CLOB,
    ingest_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ingest_user VARCHAR2(100)
);
CREATE INDEX idx_source_records_system_pk ON source_records(source_system_id, source_pk);
CREATE INDEX idx_source_records_status ON source_records(ingestion_status);
CREATE INDEX idx_source_records_email ON source_records(raw_email);
CREATE INDEX idx_source_records_phone ON source_records(raw_phone);
CREATE INDEX idx_source_records_hkid ON source_records(raw_hkid);
CREATE INDEX idx_source_records_emplid ON source_records(raw_emplid);
CREATE INDEX idx_source_records_studentid ON source_records(raw_studentid);
CREATE INDEX idx_source_records_alumniid ON source_records(raw_alumniid);

CREATE TABLE normalized_identities (
    norm_id VARCHAR2(50) PRIMARY KEY,
    source_record_id VARCHAR2(50) NOT NULL REFERENCES source_records(source_record_id),
    norm_name VARCHAR2(255),
    norm_email VARCHAR2(255),
    norm_phone VARCHAR2(80),
    norm_address VARCHAR2(500),
    norm_hkid VARCHAR2(80),
    norm_emplid VARCHAR2(80),
    norm_studentid VARCHAR2(80),
    norm_alumniid VARCHAR2(80),
    normalized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_norm_source ON normalized_identities(source_record_id);
CREATE INDEX idx_norm_ids ON normalized_identities(norm_hkid, norm_emplid, norm_studentid, norm_alumniid);

CREATE TABLE golden_records (
    golden_id VARCHAR2(50) PRIMARY KEY,
    canonical_name VARCHAR2(255),
    canonical_email VARCHAR2(255),
    canonical_phone VARCHAR2(80),
    canonical_hkid VARCHAR2(80),
    canonical_emplid VARCHAR2(80),
    canonical_studentid VARCHAR2(80),
    canonical_alumniid VARCHAR2(80),
    canonical_address VARCHAR2(500),
    person_type VARCHAR2(80),
    status VARCHAR2(30) NOT NULL,
    is_possible_duplicate CHAR(1) DEFAULT 'N' CHECK (is_possible_duplicate IN ('Y', 'N')),
    confidence_level VARCHAR2(30),
    provenance CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(100)
);
CREATE INDEX idx_golden_status ON golden_records(status);
CREATE INDEX idx_golden_email ON golden_records(canonical_email);
CREATE INDEX idx_golden_phone ON golden_records(canonical_phone);
CREATE INDEX idx_golden_hkid ON golden_records(canonical_hkid);
CREATE INDEX idx_golden_emplid ON golden_records(canonical_emplid);
CREATE INDEX idx_golden_studentid ON golden_records(canonical_studentid);
CREATE INDEX idx_golden_alumniid ON golden_records(canonical_alumniid);

CREATE TABLE golden_field_values (
    field_value_id VARCHAR2(50) PRIMARY KEY,
    golden_id VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    field_name VARCHAR2(80) NOT NULL,
    field_value VARCHAR2(1000),
    source_record_id VARCHAR2(50) REFERENCES source_records(source_record_id),
    source_system_id VARCHAR2(50) REFERENCES source_systems(system_id),
    applied_rule_id VARCHAR2(50),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_golden_field_values_golden ON golden_field_values(golden_id, field_name);

CREATE TABLE record_links (
    link_id VARCHAR2(50) PRIMARY KEY,
    source_record_id VARCHAR2(50) NOT NULL REFERENCES source_records(source_record_id),
    golden_id VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    link_status VARCHAR2(30) NOT NULL,
    link_method VARCHAR2(80) NOT NULL,
    confidence NUMBER(5,4),
    candidate_id VARCHAR2(50),
    review_task_id VARCHAR2(50),
    evidence_json CLOB,
    unlink_reason VARCHAR2(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(100),
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N'))
);
CREATE INDEX idx_record_links_source ON record_links(source_record_id, is_active);
CREATE INDEX idx_record_links_golden ON record_links(golden_id, is_active);

CREATE TABLE matching_features (
    feature_id VARCHAR2(50) PRIMARY KEY,
    feature_name VARCHAR2(80) NOT NULL,
    display_label VARCHAR2(80) NOT NULL,
    feature_type VARCHAR2(80) NOT NULL,
    is_enabled CHAR(1) DEFAULT 'Y' CHECK (is_enabled IN ('Y', 'N')),
    priority NUMBER NOT NULL,
    algorithm VARCHAR2(100) NOT NULL,
    is_auto_merge_eligible CHAR(1) DEFAULT 'Y' CHECK (is_auto_merge_eligible IN ('Y', 'N')),
    is_manual_review_only CHAR(1) DEFAULT 'N' CHECK (is_manual_review_only IN ('Y', 'N')),
    is_blocking CHAR(1) DEFAULT 'N' CHECK (is_blocking IN ('Y', 'N')),
    is_visible_in_review CHAR(1) DEFAULT 'Y' CHECK (is_visible_in_review IN ('Y', 'N')),
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_matching_features_name ON matching_features(feature_name);

CREATE TABLE matching_rules (
    rule_id VARCHAR2(50) PRIMARY KEY,
    rule_name VARCHAR2(200) NOT NULL,
    description VARCHAR2(1000),
    rule_type VARCHAR2(80) NOT NULL,
    conditions CLOB,
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    version NUMBER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(100)
);
CREATE INDEX idx_matching_rules_active ON matching_rules(is_active);

CREATE TABLE matching_rule_versions (
    version_id VARCHAR2(50) PRIMARY KEY,
    rule_id VARCHAR2(50) NOT NULL REFERENCES matching_rules(rule_id),
    version_number NUMBER NOT NULL,
    rule_snapshot CLOB NOT NULL,
    changed_by VARCHAR2(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason VARCHAR2(1000)
);
CREATE INDEX idx_matching_rule_versions_rule ON matching_rule_versions(rule_id, version_number);

CREATE TABLE threshold_settings (
    setting_id VARCHAR2(50) PRIMARY KEY,
    setting_name VARCHAR2(100) NOT NULL,
    setting_value NUMBER(8,4) NOT NULL,
    description VARCHAR2(1000),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR2(100)
);
CREATE UNIQUE INDEX idx_threshold_settings_name ON threshold_settings(setting_name);

CREATE TABLE match_candidates (
    candidate_id VARCHAR2(50) PRIMARY KEY,
    source_record_id VARCHAR2(50) NOT NULL REFERENCES source_records(source_record_id),
    golden_id VARCHAR2(50) REFERENCES golden_records(golden_id),
    total_score NUMBER(8,6) NOT NULL,
    decision_hint VARCHAR2(50),
    rank_order NUMBER DEFAULT 1,
    has_tier1_conflict CHAR(1) DEFAULT 'N' CHECK (has_tier1_conflict IN ('Y', 'N')),
    has_multi_match CHAR(1) DEFAULT 'N' CHECK (has_multi_match IN ('Y', 'N')),
    has_low_gap CHAR(1) DEFAULT 'N' CHECK (has_low_gap IN ('Y', 'N')),
    source_trust VARCHAR2(30),
    evidence_summary CLOB,
    scoring_version VARCHAR2(80),
    rule_version VARCHAR2(80),
    scored_by VARCHAR2(100),
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_match_candidates_source ON match_candidates(source_record_id, rank_order);
CREATE INDEX idx_match_candidates_golden ON match_candidates(golden_id);

CREATE TABLE match_candidate_features (
    feature_id VARCHAR2(50) PRIMARY KEY,
    candidate_id VARCHAR2(50) NOT NULL REFERENCES match_candidates(candidate_id),
    feature_name VARCHAR2(80) NOT NULL,
    feature_type VARCHAR2(80) NOT NULL,
    display_label VARCHAR2(80),
    source_value VARCHAR2(1000),
    golden_value VARCHAR2(1000),
    normalized_source_value VARCHAR2(1000),
    normalized_golden_value VARCHAR2(1000),
    similarity_algorithm VARCHAR2(100),
    similarity_score NUMBER(8,6),
    priority NUMBER,
    calculated_weight NUMBER(8,6),
    weighted_score NUMBER(8,6),
    is_match CHAR(1) DEFAULT 'N' CHECK (is_match IN ('Y', 'N')),
    is_conflict CHAR(1) DEFAULT 'N' CHECK (is_conflict IN ('Y', 'N')),
    is_blocking_feature CHAR(1) DEFAULT 'N' CHECK (is_blocking_feature IN ('Y', 'N')),
    is_visible_in_review CHAR(1) DEFAULT 'Y' CHECK (is_visible_in_review IN ('Y', 'N')),
    evidence_json CLOB
);
CREATE INDEX idx_match_candidate_features_candidate ON match_candidate_features(candidate_id, feature_name);

CREATE TABLE rule_simulations (
    simulation_id VARCHAR2(50) PRIMARY KEY,
    simulation_name VARCHAR2(200) NOT NULL,
    rule_snapshot CLOB NOT NULL,
    status VARCHAR2(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR2(100)
);
CREATE TABLE rule_simulation_results (
    result_id VARCHAR2(50) PRIMARY KEY,
    simulation_id VARCHAR2(50) NOT NULL REFERENCES rule_simulations(simulation_id),
    source_record_id VARCHAR2(50) NOT NULL REFERENCES source_records(source_record_id),
    old_decision VARCHAR2(50),
    new_decision VARCHAR2(50),
    old_score NUMBER(8,6),
    new_score NUMBER(8,6),
    changed CHAR(1) DEFAULT 'N' CHECK (changed IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_rule_sim_results_sim ON rule_simulation_results(simulation_id);

CREATE TABLE manual_review_tasks (
    task_id VARCHAR2(50) PRIMARY KEY,
    source_record_id VARCHAR2(50) NOT NULL REFERENCES source_records(source_record_id),
    candidate_golden_ids CLOB,
    best_confidence NUMBER(8,6),
    priority VARCHAR2(30),
    status VARCHAR2(30) NOT NULL,
    reason_code VARCHAR2(80),
    assigned_to VARCHAR2(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    notes CLOB,
    safety_flags CLOB
);
CREATE INDEX idx_manual_review_tasks_status ON manual_review_tasks(status, priority);

CREATE TABLE manual_review_decisions (
    decision_id VARCHAR2(50) PRIMARY KEY,
    task_id VARCHAR2(50) NOT NULL REFERENCES manual_review_tasks(task_id),
    reviewer VARCHAR2(100) NOT NULL,
    decision VARCHAR2(80) NOT NULL,
    selected_golden_id VARCHAR2(50) REFERENCES golden_records(golden_id),
    notes CLOB,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_manual_review_decisions_task ON manual_review_decisions(task_id, decided_at);

CREATE TABLE golden_duplicate_candidates (
    duplicate_id VARCHAR2(50) PRIMARY KEY,
    golden_id_a VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    golden_id_b VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    similarity_score NUMBER(8,6),
    status VARCHAR2(30) NOT NULL,
    detection_method VARCHAR2(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
CREATE INDEX idx_duplicate_status ON golden_duplicate_candidates(status);

CREATE TABLE golden_merge_events (
    merge_event_id VARCHAR2(50) PRIMARY KEY,
    source_golden_id VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    target_golden_id VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    merged_by VARCHAR2(100),
    merge_reason CLOB,
    merged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    merged_source_records CLOB
);

CREATE TABLE survivorship_rules (
    rule_id VARCHAR2(50) PRIMARY KEY,
    field_name VARCHAR2(80) NOT NULL,
    rule_name VARCHAR2(200) NOT NULL,
    strategy VARCHAR2(80) NOT NULL,
    priority_source_systems CLOB,
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    version NUMBER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_survivorship_rules_field ON survivorship_rules(field_name, is_active);

CREATE TABLE survivorship_rule_versions (
    version_id VARCHAR2(50) PRIMARY KEY,
    rule_id VARCHAR2(50) NOT NULL REFERENCES survivorship_rules(rule_id),
    version_number NUMBER NOT NULL,
    rule_snapshot CLOB NOT NULL,
    changed_by VARCHAR2(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_survivorship_rule_versions_rule ON survivorship_rule_versions(rule_id, version_number);

CREATE TABLE survivorship_previews (
    preview_id VARCHAR2(50) PRIMARY KEY,
    golden_id VARCHAR2(50) NOT NULL REFERENCES golden_records(golden_id),
    field_name VARCHAR2(80) NOT NULL,
    current_value VARCHAR2(1000),
    preview_value VARCHAR2(1000),
    applied_rule_id VARCHAR2(50),
    preview_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_survivorship_previews_golden ON survivorship_previews(golden_id, field_name);

CREATE TABLE merge_history (
    event_id VARCHAR2(50) PRIMARY KEY,
    event_type VARCHAR2(80) NOT NULL,
    actor VARCHAR2(100),
    source_record_id VARCHAR2(50) REFERENCES source_records(source_record_id),
    golden_id VARCHAR2(50) REFERENCES golden_records(golden_id),
    details CLOB,
    event_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_merge_history_golden ON merge_history(golden_id, event_ts);
CREATE INDEX idx_merge_history_source ON merge_history(source_record_id, event_ts);

CREATE TABLE audit_events (
    event_id VARCHAR2(50) PRIMARY KEY,
    event_type VARCHAR2(80) NOT NULL,
    entity_type VARCHAR2(80) NOT NULL,
    entity_id VARCHAR2(50) NOT NULL,
    actor VARCHAR2(100),
    action VARCHAR2(80),
    old_value CLOB,
    new_value CLOB,
    event_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR2(64),
    notes VARCHAR2(1000)
);
CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id, event_ts);
CREATE INDEX idx_audit_events_event_type ON audit_events(event_type, event_ts);

CREATE TABLE app_users (
    user_id VARCHAR2(50) PRIMARY KEY,
    username VARCHAR2(100) NOT NULL,
    display_name VARCHAR2(200),
    email VARCHAR2(255),
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_app_users_username ON app_users(username);

CREATE TABLE app_roles (
    role_id VARCHAR2(50) PRIMARY KEY,
    role_name VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    permissions CLOB
);
CREATE UNIQUE INDEX idx_app_roles_name ON app_roles(role_name);

CREATE TABLE app_user_roles (
    user_role_id VARCHAR2(50) PRIMARY KEY,
    user_id VARCHAR2(50) NOT NULL REFERENCES app_users(user_id),
    role_id VARCHAR2(50) NOT NULL REFERENCES app_roles(role_id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR2(100)
);
CREATE INDEX idx_app_user_roles_user ON app_user_roles(user_id, role_id);

CREATE TABLE rebatch_jobs (
    job_id VARCHAR2(50) PRIMARY KEY,
    source_system_id VARCHAR2(50) NOT NULL REFERENCES source_systems(system_id),
    batch_id VARCHAR2(50) REFERENCES ingestion_batches(batch_id),
    status VARCHAR2(30) NOT NULL,
    reason VARCHAR2(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR2(100)
);
CREATE INDEX idx_rebatch_jobs_status ON rebatch_jobs(status);

INSERT INTO source_systems (system_id, name, description, trust_level, is_internal, auto_merge_allowed, is_active, created_at) VALUES
('SYS-001', 'HR', 'Internal HR master for employees and staff identities.', 'trusted', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP);
INSERT INTO source_systems VALUES ('SYS-002', 'SIS', 'Student Information System for active students and applicants.', 'trusted', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP);
INSERT INTO source_systems VALUES ('SYS-003', 'Alumni', 'Alumni engagement platform with post-graduation attributes.', 'trusted', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP);
INSERT INTO source_systems VALUES ('SYS-004', 'CRM', 'External CRM and outreach contacts from marketing workflows.', 'standard', 'N', 'Y', 'Y', CURRENT_TIMESTAMP);
INSERT INTO source_systems VALUES ('SYS-005', 'ThirdParty', 'Untrusted third-party enrichment feed requiring corroboration.', 'untrusted', 'N', 'N', 'Y', CURRENT_TIMESTAMP);

INSERT INTO matching_features (feature_id, feature_name, display_label, feature_type, is_enabled, priority, algorithm, is_auto_merge_eligible, is_manual_review_only, is_blocking, is_visible_in_review, is_active, created_at, updated_at) VALUES
('MF-001', 'hkid', 'HKID', 'identifier', 'Y', 100, 'exact_match', 'Y', 'N', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-002', 'emplid', 'EmplId', 'identifier', 'Y', 100, 'exact_match', 'Y', 'N', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-003', 'studentid', 'StudentId', 'identifier', 'Y', 100, 'exact_match', 'Y', 'N', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-004', 'alumniid', 'AlumniId', 'identifier', 'Y', 100, 'exact_match', 'Y', 'N', 'Y', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-005', 'email', 'Email', 'contact', 'Y', 80, 'exact_match', 'Y', 'N', 'N', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-006', 'phone', 'Phone', 'contact', 'Y', 60, 'phone_exact_or_last8', 'Y', 'N', 'N', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-007', 'name', 'Name', 'profile', 'Y', 40, 'sequence_matcher', 'Y', 'N', 'N', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO matching_features VALUES ('MF-008', 'address', 'Address', 'profile', 'Y', 20, 'sequence_matcher', 'N', 'N', 'N', 'Y', 'Y', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO threshold_settings (setting_id, setting_name, setting_value, description, updated_at, updated_by) VALUES ('TH-001', 'auto_merge', 0.85, 'Auto merge threshold', CURRENT_TIMESTAMP, 'seed');
INSERT INTO threshold_settings VALUES ('TH-002', 'manual_review', 0.50, 'Manual review threshold', CURRENT_TIMESTAMP, 'seed');
INSERT INTO threshold_settings VALUES ('TH-003', 'new_golden', 0.50, 'New golden threshold', CURRENT_TIMESTAMP, 'seed');
INSERT INTO threshold_settings VALUES ('TH-004', 'multi_match_gap', 0.10, 'Multi-candidate gap threshold', CURRENT_TIMESTAMP, 'seed');

INSERT INTO app_roles (role_id, role_name, description, permissions) VALUES ('ROLE-001', 'Viewer', 'Read-only access', '[]');
INSERT INTO app_roles VALUES ('ROLE-002', 'Reviewer', 'Manual review operator', '[]');
INSERT INTO app_roles VALUES ('ROLE-003', 'Data Steward', 'Data correction and merge authority', '[]');
INSERT INTO app_roles VALUES ('ROLE-004', 'Rule Admin', 'Rule configuration authority', '[]');
INSERT INTO app_roles VALUES ('ROLE-005', 'System Admin', 'Full system administration', '[]');
