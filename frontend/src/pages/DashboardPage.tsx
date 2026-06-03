import { authStore } from '../features/auth/authStore';

export function DashboardPage() {
  const { user } = authStore.getState();

  return (
    <section className="rounded-2xl bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">Dashboard</p>
      <h2 className="mt-3 text-3xl font-bold text-slate-950">Welcome, {user?.full_name}</h2>
      <p className="mt-4 max-w-2xl text-slate-600">
        Authentication and RBAC foundation is active. Business modules are intentionally placeholder-only in Sprint 2.
      </p>
    </section>
  );
}
