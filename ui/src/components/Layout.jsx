import { createContext, useContext, useMemo, useState } from 'react';
import { NavLink } from 'react-router-dom';

const RoleContext = createContext({ role: 'Reviewer' });

const NAV_SECTIONS = [
  {
    title: 'Overview',
    links: [
      ['Dashboard', '/'],
      ['Audit History', '/audit'],
    ],
  },
  {
    title: 'Ingestion',
    links: [
      ['New Source Record', '/ingestion/new'],
      ['Batch Runs', '/ingestion/batches'],
      ['Source Search', '/sources'],
    ],
  },
  {
    title: 'Resolution',
    links: [
      ['Golden Search', '/golden'],
      ['Manual Review Queue', '/manual-review'],
      ['Duplicate Golden Queue', '/duplicates'],
    ],
  },
  {
    title: 'Configuration',
    links: [
      ['Matching Features', '/settings/matching-features'],
      ['Matching Rules', '/settings/matching-rules'],
      ['Rule Simulation', '/settings/rule-simulation'],
      ['Thresholds', '/settings/thresholds'],
      ['Survivorship Rules', '/settings/survivorship'],
      ['Survivorship Preview', '/settings/survivorship-preview'],
      ['Source Systems', '/settings/source-systems'],
    ],
  },
];

const ROLES = ['Viewer', 'Reviewer', 'Data Steward', 'Rule Admin', 'System Admin'];

export function useRole() {
  return useContext(RoleContext);
}

export default function Layout({ children }) {
  const [role, setRole] = useState('Reviewer');
  const contextValue = useMemo(() => ({ role, setRole }), [role]);

  return (
    <RoleContext.Provider value={contextValue}>
      <div className="layout-shell">
        <aside className="sidebar">
          <div>
            <h1>IRE Console</h1>
            <p className="muted-text">Identity Resolution Engine proof of concept</p>
          </div>
          {NAV_SECTIONS.map((section) => (
            <div key={section.title} className="nav-group">
              <div className="nav-heading">{section.title}</div>
              {section.links.map(([label, to]) => (
                <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </aside>
        <div className="main-shell">
          <header className="topbar card">
            <div>
              <strong>Current role:</strong> {role}
            </div>
            <label className="inline-field">
              <span>Role selector</span>
              <select value={role} onChange={(event) => setRole(event.target.value)}>
                {ROLES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </header>
          <main className="page-shell">{children}</main>
        </div>
      </div>
    </RoleContext.Provider>
  );
}
