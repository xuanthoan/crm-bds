import { getCurrentUser } from '../features/auth/authStore';

export function DashboardPage() {
  const user = getCurrentUser();

  return (
    <section className="page-card">
      <p className="eyebrow">Dashboard</p>
      <h1>Welcome back, {user?.full_name ?? 'Admin'}</h1>
      <p>Authentication and RBAC foundations are active. Business dashboard widgets will be added in later sprints.</p>
    </section>
  );
}
