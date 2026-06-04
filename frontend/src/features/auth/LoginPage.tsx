import { FormEvent, useState } from 'react';

import { navigateTo } from '../../routes/AppRoutes';
import { login } from './api';
import { setSession } from './authStore';

export function LoginPage() {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('Admin@123456');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await login(email, password);
      setSession(response.data.access_token, response.data.refresh_token, response.data.user);
      navigateTo('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <p className="eyebrow">CRM BDS</p>
        <h1>Sign in to your workspace</h1>
        <p className="muted">Use the default Sprint 2 admin account to verify authentication and RBAC.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Email
            <input
              type="email"
              placeholder="admin@example.com"
              value={email}
              onChange={(event: any) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              placeholder="Admin@123456"
              value={password}
              onChange={(event: any) => setPassword(event.target.value)}
              required
            />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}
