import { NavLink } from 'react-router-dom';
import { useMemo } from 'react';
import { useAuth } from '../../context/AuthContext.jsx';

const Sidebar = () => {
  const { user } = useAuth();

  const links = useMemo(() => {
    const baseLinks = [
      { label: 'Tableau de bord', to: '/', icon: '📊' },
      { label: 'Nouvelle analyse', to: '/analysis/new', icon: '🧪' },
      { label: 'Rapports', to: '/reports', icon: '🗂️' },
      { label: 'Extensions', to: '/extensions', icon: '🧩' },
      { label: 'Paramètres', to: '/settings', icon: '⚙️' }
    ];

    if (user?.role === 'admin') {
      baseLinks.push({ label: 'Utilisateurs', to: '/admin/users', icon: '👥' });
    }

    return baseLinks;
  }, [user]);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>CheckMe</h1>
        <span className="tag">
          {user?.role === 'admin' ? 'Admin Console' : 'Analyst Workspace'}
        </span>
      </div>

      <nav className="sidebar-nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            end={link.to === '/'}
          >
            <span aria-hidden="true">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
