import { FormEvent, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { login } from './api';
import { authStore, useAuth } from './authStore';

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('Admin@123456');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { accessToken } = useAuth();

  if (accessToken) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const response = await login(email, password);
      authStore.setAuth({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        user: response.data.user,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl shadow-slate-200">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-blue-600">CRM BDS</p>
        <h1 className="mt-3 text-3xl font-bold text-slate-950">Sign in</h1>
        <p className="mt-2 text-sm text-slate-500">Use the default Sprint 2 admin account to verify authentication.</p>

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none ring-blue-600 transition focus:ring-2"
              type="email"
              value={email}
              placeholder="admin@example.com"
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3 outline-none ring-blue-600 transition focus:ring-2"
              type="password"
              value={password}
              placeholder="Admin@123456"
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

          <button
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}
