import type { ReactNode } from 'react';

import { logout } from '../features/auth/api';
import { can, clearSession, getCurrentUser, getRefreshToken } from '../features/auth/authStore';
import { navigateTo } from '../routes/AppRoutes';

type AppLayoutProps = {
  children?: ReactNode;
  currentPath: string;
};

const sidebarItems = [
  { label: 'Dashboard', path: '/dashboard', permission: null },
  { label: 'Customers', path: '/customers', permission: 'customers.view.own' },
  { label: 'Properties', path: '/properties', permission: 'inventory.view.available' },
  { label: 'Deals', path: '/deals', permission: 'deals.view.own' },
  { label: 'Reports', path: '/reports', permission: 'reports.view.own' },
];

export function AppLayout({ children, currentPath }: AppLayoutProps) {
  const user = getCurrentUser();

  async function handleLogout() {
    const refreshToken = getRefreshToken();
    try {
      await logout(refreshToken);
    } catch {
      // Session is cleared locally even if the server-side revoke request fails.
    } finally {
      clearSession();
      navigateTo('/login');
    }
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">CRM BDS</div>
        <nav>
          {sidebarItems
            .filter((item) => !item.permission || can(item.permission))
            .map((item) => (
              <a
                key={item.path}
                href={item.path}
                className={currentPath === item.path ? 'active' : ''}
                onClick={(event: any) => {
                  event.preventDefault();
                  navigateTo(item.path);
                }}
              >
                {item.label}
              </a>
            ))}
        </nav>
      </aside>
      <div className="content-shell">
        <header className="topbar">
          <div>
            <strong>{user?.full_name ?? 'Authenticated User'}</strong>
            <span>{user?.roles.join(', ')}</span>
          </div>
          <button type="button" onClick={handleLogout} className="secondary-button">
            Logout
          </button>
        </header>
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
