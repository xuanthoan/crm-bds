import type { ReactNode } from 'react';

import { logout } from '../features/auth/api';
import { VIEW_PERMISSIONS } from '../features/leads/constants';
import { can, clearSession, getCurrentUser, getRefreshToken } from '../features/auth/authStore';
import { navigateTo } from '../routes/AppRoutes';

type AppLayoutProps = {
  children?: ReactNode;
  currentPath: string;
};

const adminItems = [
  { label: 'Người dùng', path: '/admin/users', permission: 'users.view' },
  { label: 'Vai trò', path: '/admin/roles', permission: 'roles.view' },
  { label: 'Quyền', path: '/admin/permissions', permission: 'permissions.view' },
];

export function AppLayout({ children, currentPath }: AppLayoutProps) {
  const user = getCurrentUser();
  const visibleAdminItems = adminItems.filter((item) => can(item.permission));
  const canViewLeads = VIEW_PERMISSIONS.some(can);

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

  function renderLink(label: string, path: string) {
    return (
      <a
        href={path}
        className={currentPath === path || (path === '/leads' && currentPath.startsWith('/leads/')) ? 'active' : ''}
        onClick={(event: any) => {
          event.preventDefault();
          navigateTo(path);
        }}
      >
        {label}
      </a>
    );
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">CRM BDS</div>
        <nav>
          {renderLink('Dashboard', '/dashboard')}
          {canViewLeads && <div className="nav-section"><span>CRM</span><div>{renderLink('Leads / Khách tiềm năng', '/leads')}</div></div>}
          {visibleAdminItems.length > 0 && (
            <div className="nav-section">
              <span>Quản trị hệ thống</span>
              {visibleAdminItems.map((item) => <div key={item.path}>{renderLink(item.label, item.path)}</div>)}
            </div>
          )}
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
