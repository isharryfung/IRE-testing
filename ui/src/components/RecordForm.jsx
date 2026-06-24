import React, { useState } from 'react';

const EMPTY_FORM = {
  sourceSystem: 'HR',
  sourcePk: '',
  name: '',
  email: '',
  phone: '',
  address: '',
  hkid: '',
  emplid: '',
  studentid: '',
  alumniid: '',
};

export default function RecordForm({ includeSourcePk = true, submitLabel, onSubmit }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(form, () => setForm(EMPTY_FORM));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stack">
      <div className="grid two-col">
        <label>Source System<input value={form.sourceSystem} onChange={(e) => updateField('sourceSystem', e.target.value)} required /></label>
        {includeSourcePk && <label>Source Primary Key<input value={form.sourcePk} onChange={(e) => updateField('sourcePk', e.target.value)} required /></label>}
        <label>Name<input value={form.name} onChange={(e) => updateField('name', e.target.value)} /></label>
        <label>Email<input value={form.email} onChange={(e) => updateField('email', e.target.value)} /></label>
        <label>Phone<input value={form.phone} onChange={(e) => updateField('phone', e.target.value)} /></label>
        <label>Address<input value={form.address} onChange={(e) => updateField('address', e.target.value)} /></label>
        <label>HKID<input value={form.hkid} onChange={(e) => updateField('hkid', e.target.value)} /></label>
        <label>EmplId<input value={form.emplid} onChange={(e) => updateField('emplid', e.target.value)} /></label>
        <label>Student ID<input value={form.studentid} onChange={(e) => updateField('studentid', e.target.value)} /></label>
        <label>Alumni ID<input value={form.alumniid} onChange={(e) => updateField('alumniid', e.target.value)} /></label>
      </div>
      <button disabled={submitting} type="submit">{submitting ? 'Submitting...' : submitLabel}</button>
    </form>
  );
}
