export default function SearchFilters({ filters = [], values = {}, onChange }) {
  return (
    <div className="filter-grid card subtle">
      {filters.map((filter) => (
        <label key={filter.name} className="field">
          <span>{filter.label}</span>
          {filter.type === 'select' ? (
            <select value={values[filter.name] || ''} onChange={(event) => onChange(filter.name, event.target.value)}>
              <option value="">All</option>
              {(filter.options || []).map((option) => (
                <option key={option.value || option} value={option.value || option}>
                  {option.label || option}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={filter.type || 'text'}
              value={values[filter.name] || ''}
              placeholder={filter.placeholder || ''}
              onChange={(event) => onChange(filter.name, event.target.value)}
            />
          )}
        </label>
      ))}
    </div>
  );
}
