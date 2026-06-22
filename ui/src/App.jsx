import React, { useState } from "react";
import ReviewTask from "./ReviewTask.jsx";
import initialTasks from "./data/tasks.json";

export default function App() {
  const [tasks, setTasks] = useState(initialTasks);
  const [selectedId, setSelectedId] = useState(tasks[0]?.task_id ?? null);

  const selectedTask = tasks.find((t) => t.task_id === selectedId) ?? null;

  function handleDecision(taskId, decision) {
    setTasks((prev) =>
      prev.map((t) => (t.task_id === taskId ? { ...t, status: decision } : t))
    );
  }

  const pendingCount = tasks.filter((t) => t.status === "pending").length;

  return (
    <main className="app-shell">
      <h1>Identity Resolution Engine — Manual Review</h1>
      <p>
        <strong>{pendingCount}</strong> task{pendingCount !== 1 ? "s" : ""} pending review.
      </p>

      <div style={{ display: "flex", gap: "1.5rem", alignItems: "flex-start" }}>
        {/* Queue sidebar */}
        <aside style={{ minWidth: 200 }}>
          <h3 style={{ marginBottom: "0.5rem" }}>Review Queue</h3>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {tasks.map((t) => (
              <li
                key={t.task_id}
                onClick={() => setSelectedId(t.task_id)}
                style={{
                  padding: "8px 12px",
                  marginBottom: 4,
                  cursor: "pointer",
                  borderRadius: 4,
                  background: t.task_id === selectedId ? "#0d6efd" : "#f0f0f0",
                  color: t.task_id === selectedId ? "#fff" : "#333",
                  opacity: t.status !== "pending" ? 0.6 : 1,
                }}
              >
                <div style={{ fontWeight: 600 }}>{t.task_id}</div>
                <div style={{ fontSize: "0.8em" }}>
                  {(t.confidence * 100).toFixed(1)}% · {t.status}
                </div>
              </li>
            ))}
          </ul>
        </aside>

        {/* Detail panel */}
        <section style={{ flex: 1 }}>
          <ReviewTask task={selectedTask} onDecision={handleDecision} />
        </section>
      </div>
    </main>
  );
}

