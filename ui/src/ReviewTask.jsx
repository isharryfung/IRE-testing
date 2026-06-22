import React from "react";

const STATUS_LABELS = {
  pending: "⏳ Pending Review",
  approved: "✅ Approved",
  rejected: "❌ Rejected",
  create_new: "🆕 Create New",
};

function FieldRow({ label, left, right, sim }) {
  const simPct = sim != null ? `${(sim * 100).toFixed(0)}%` : "—";
  const highlight =
    sim === 1.0
      ? "#d4edda"
      : sim != null && sim >= 0.7
      ? "#fff3cd"
      : sim != null
      ? "#f8d7da"
      : "#f9f9f9";
  return (
    <tr style={{ backgroundColor: highlight }}>
      <td style={{ fontWeight: 600, padding: "4px 8px" }}>{label}</td>
      <td style={{ padding: "4px 8px" }}>{left || "—"}</td>
      <td style={{ padding: "4px 8px" }}>{right || "—"}</td>
      <td style={{ padding: "4px 8px", textAlign: "center" }}>{simPct}</td>
    </tr>
  );
}

const FIELDS = [
  { key: "name", label: "Name", simKey: "name" },
  { key: "email", label: "Email", simKey: "email" },
  { key: "phone", label: "Phone", simKey: "phone" },
  { key: "hkid", label: "HKID", simKey: "id" },
  { key: "emplid", label: "Empl ID", simKey: "id" },
  { key: "studentid", label: "Student ID", simKey: "id" },
  { key: "address", label: "Address", simKey: "address" },
];

export default function ReviewTask({ task, onDecision }) {
  if (!task) {
    return <p style={{ color: "#888" }}>Select a task from the queue.</p>;
  }

  const { source_record, candidate, similarities, confidence, reason, status } = task;
  const confidencePct = `${(confidence * 100).toFixed(1)}%`;
  const badge =
    confidence >= 0.85
      ? "#28a745"
      : confidence >= 0.5
      ? "#ffc107"
      : "#dc3545";

  return (
    <div className="review-task">
      <h2>
        Task {task.task_id}{" "}
        <span style={{ fontSize: "0.8em", color: "#666" }}>
          {STATUS_LABELS[status] || status}
        </span>
      </h2>

      <p>
        <strong>Confidence:</strong>{" "}
        <span
          style={{
            background: badge,
            color: "#fff",
            borderRadius: 4,
            padding: "2px 8px",
          }}
        >
          {confidencePct}
        </span>
        &nbsp;— {reason}
      </p>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          marginBottom: "1rem",
          fontSize: "0.9em",
        }}
      >
        <thead>
          <tr style={{ background: "#e9ecef" }}>
            <th style={{ padding: "6px 8px", textAlign: "left" }}>Field</th>
            <th style={{ padding: "6px 8px", textAlign: "left" }}>
              Incoming ({source_record.record_id})
            </th>
            <th style={{ padding: "6px 8px", textAlign: "left" }}>
              Golden ({candidate.record_id})
            </th>
            <th style={{ padding: "6px 8px", textAlign: "center" }}>Sim</th>
          </tr>
        </thead>
        <tbody>
          {FIELDS.map(({ key, label, simKey }) => (
            <FieldRow
              key={key}
              label={label}
              left={source_record[key]}
              right={candidate[key]}
              sim={similarities[simKey]}
            />
          ))}
        </tbody>
      </table>

      {status === "pending" && (
        <div className="decision-panel">
          <button
            style={{ background: "#28a745", color: "#fff", marginRight: 8 }}
            onClick={() => onDecision(task.task_id, "approved")}
          >
            ✅ Approve Merge
          </button>
          <button
            style={{ background: "#dc3545", color: "#fff", marginRight: 8 }}
            onClick={() => onDecision(task.task_id, "rejected")}
          >
            ❌ Reject Merge
          </button>
          <button
            style={{ background: "#6c757d", color: "#fff" }}
            onClick={() => onDecision(task.task_id, "create_new")}
          >
            🆕 Create New Golden
          </button>
        </div>
      )}
    </div>
  );
}
