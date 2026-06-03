import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { logout } from '../features/auth/api';
import { authStore, can, useAuth } from '../features/auth/authStore';

const sidebarItems = [
  { label: 'Dashboard', to: '/dashboard', permission: null },
  { label: 'Customers', to: '/customers', permission: 'customers.view.own' },
  { label: 'Properties', to: '/properties', permission: 'inventory.view.available' },
  { label: 'Deals', to: '/deals', permission: 'deals.view.own' },
  { label: 'Reports', to: '/reports', permission: 'reports.view.own' },
];

export function AppLayout() {
  const navigate = useNavigate();
  const { user, refreshToken } = useAuth();

  async function handleLogout() {
    try {
      await logout(refreshToken);
    } finally {
      authStore.clear();
      navigate('/login', { replace: true });
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="hidden w-72 border-r border-slate-200 bg-white p-6 md:block">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-blue-600">CRM BDS</p>
          <h1 className="mt-2 text-xl font-bold text-slate-950">Real Estate CRM</h1>
        </div>

        <nav className="mt-10 space-y-2">
          {sidebarItems
            .filter((item) => item.permission === null || can(item.permission, user))
            .map((item) => (
              <NavLink
                className={({ isActive }) =>
                  `block rounded-lg px-4 py-3 text-sm font-medium transition ${
                    isActive ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
                  }`
                }
                key={item.to}
                to={item.to}
              >
                {item.label}
              </NavLink>
            ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <p className="text-sm text-slate-500">Signed in as</p>
            <p className="font-semibold text-slate-950">{user?.full_name ?? 'Unknown user'}</p>
          </div>
          <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" onClick={handleLogout} type="button">
            Logout
          </button>
        </header>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
