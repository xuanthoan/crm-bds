import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main className="app-shell">
      <section className="foundation-card">
        <p className="eyebrow">CRM BDS</p>
        <h1>Project foundation is ready</h1>
        <p>
          React, FastAPI, PostgreSQL, Redis, and Docker are wired for Sprint 1.
          Business modules will be added in later sprints.
        </p>
      </section>
    </main>
  );
}

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
