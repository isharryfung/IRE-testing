# Identity Resolution Engine Design

## Purpose
The IRE resolves records from multiple systems to determine whether they represent the same real person, then links them to a golden record with auditability.

## Core entities
- **Source record**: raw ingested payload from source system (immutable input).
- **Normalized identity**: cleaned/normalized matching attributes derived from source record.
- **Golden record**: canonical resolved person profile.
- **Record link**: relationship from source record to golden record with method/confidence/evidence.

## Identity attribute tiers
- **Tier 1 (strong IDs)**: HKID, EmplId, Student ID, Alumni ID.
- **Tier 2 (supporting profile/contact)**: Name, Email, Mobile, Address.

## Matching strategy
1. Normalize incoming record.
2. Candidate generation using exact IDs, email, phone, and name blocking.
3. Deterministic rules:
   - Trusted internal Tier 1 exact match + no conflict => auto-merge.
   - Third-party Tier 1 exact match requires supporting evidence.
   - Tier 1 conflict blocks auto-merge.
4. Probabilistic scoring with dynamic weights:
   - `weight(field) = priority(field) / sum(priorities of present fields)`
   - weighted confidence from field similarities.

## Safety checks
Before auto-merge, enforce:
- Tier 1 conflict check.
- Multiple high-confidence candidate risk.
- Low score gap between top 2 candidates.

## Decision outcomes
- **auto-merge** (`confidence >= auto threshold`, default `0.85`, and safe)
- **manual-review** (`confidence >= manual threshold`, default `0.50`, or blocked by safety)
- **new-golden-record** (below manual threshold or no viable candidate)

## Manual review workflow
1. Create review task with candidate/evidence payload.
2. Reviewer chooses merge/new/reject/escalate.
3. Persist decision and apply linkage/merge updates.
4. Keep full decision history for audit.

## Survivorship
Canonical values are chosen by configurable strategies (trust-best-source, most-recent, most-complete, manual override), with provenance tracked at field level.

## Rebatch lifecycle
Scheduled/triggered rebatch jobs:
- Re-score unmatched or previously reviewed records.
- Re-evaluate with updated rules/thresholds.
- Generate fresh candidate evidence and review tasks where needed.

## Final decision flow
Rules + scoring + safety checks + human review + provenance are all required; confidence alone is not sufficient for production-quality decisions.
