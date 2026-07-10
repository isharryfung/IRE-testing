const STEPS = [
  { key: 'ingested', label: 'Ingested' },
  { key: 'normalized', label: 'Normalized' },
  { key: 'matched', label: 'Matched' },
  { key: 'decision', label: 'Decision' },
  { key: 'auto_merged', label: 'Auto-merged' },
  { key: 'manual_review', label: 'Manual Review' },
  { key: 'new_golden', label: 'New Golden' },
];

export default function ProcessStepper({ currentStep = 'decision', counts = {} }) {
  const activeIndex = Math.max(STEPS.findIndex((step) => step.key === currentStep), 0);

  return (
    <div className="stepper">
      {STEPS.map((step, index) => (
        <div key={step.key} className={`step ${index <= activeIndex ? 'active' : ''}`}>
          <div className="step-dot" />
          <div>
            <div className="step-label">{step.label}</div>
            <div className="step-count">{counts[step.key] ?? 0}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
