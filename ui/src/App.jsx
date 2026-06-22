import React, { useMemo, useState } from "react";

const sampleRequest = {
  incoming: {
    record_id: "IN-001",
    source_type: "third_party",
    name: "John Smith",
    email: "jsmith@ust.hk",
    phone: "+852-555-123-4567",
    address: "Clear Water Bay"
  },
  golden_records: [
    {
      record_id: "GR-001",
      source_type: "internal",
      name: "John Michael Smith",
      email: "jsmith@ust.hk",
      phone: "+8525551234567",
      hkid: "A123456(7)",
      emplid: "E1001",
      address: "Clear Water Bay"
    }
  ]
};

function localScore(request) {
  const incoming = request.incoming;
  const golden = request.golden_records[0];
  const exactEmail = incoming.email?.toLowerCase() === golden.email?.toLowerCase() ? 1 : 0;
  const phoneMatch = incoming.phone?.replace(/\D/g, "") === golden.phone?.replace(/\D/g, "") ? 1 : 0;
  const confidence = 0.5714 * exactEmail + 0.4286 * phoneMatch;
  return confidence >= 0.85 ? "auto_merge" : confidence >= 0.5 ? "manual_review" : "create_new_golden_record";
}

export default function App() {
  const [payload, setPayload] = useState(JSON.stringify(sampleRequest, null, 2));
  const decision = useMemo(() => localScore(JSON.parse(payload)), [payload]);

  return (
    <main className="app-shell">
      <h1>Identity Resolution Engine</h1>
      <p>Prototype UI for reviewing an incoming record, candidate golden records, and the resulting match decision.</p>
      <section>
        <h2>Sample Match Request</h2>
        <textarea value={payload} onChange={(event) => setPayload(event.target.value)} rows={18} />
      </section>
      <section className="decision-card">
        <h2>Local Preview Decision</h2>
        <strong>{decision}</strong>
        <p>Use the FastAPI <code>/match</code> endpoint for authoritative scoring.</p>
      </section>
    </main>
  );
}
