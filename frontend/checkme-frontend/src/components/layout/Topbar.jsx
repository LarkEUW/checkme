import { useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { useTheme } from '../../context/ThemeContext.jsx';

const routeTitles = {
  '/': 'Tableau de bord',
  '/analysis/new': 'Nouvelle analyse',
  '/reports': 'Rapports',
  '/extensions': 'Catalogue des extensions',
  '/settings': 'Centre de configuration',
  '/admin/users': 'Administration des utilisateurs'
};

const Topbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const title = useMemo(() => {
    const pathname = location.pathname;
    if (pathname.startsWith('/reports/') && pathname.split('/').length === 3) {
      return 'Rapport d’analyse';
    }
    return routeTitles[pathname] || 'CheckMe';
  }, [location.pathname]);

  const handleNewAnalysis = useCallback(() => {
    navigate('/analysis/new');
  }, [navigate]);

  return (
    <header className="topbar">
      <div>
        <h2 style={{ margin: 0, fontSize: '1.3rem' }}>{title}</h2>
        <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: '0.9rem' }}>
          {user?.role === 'admin'
            ? 'Contrôlez les risques et les utilisateurs de la plateforme.'
            : 'Évaluez les extensions et collaborez avec votre équipe SOC.'}
        </p>
      </div>
      <div className="actions">
        <button type="button" className="button ghost" onClick={toggleTheme}>
          {theme === 'light' ? '🌙 Mode sombre' : '☀️ Mode clair'}
        </button>
        <button type="button" className="button ghost" onClick={handleNewAnalysis}>
          ⊕ Nouvelle analyse
        </button>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <strong style={{ fontSize: '0.95rem' }}>{user?.full_name || user?.email}</strong>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-muted)' }}>
            {user?.role === 'admin' ? 'Administrateur' : 'Analyste'}
          </span>
        </div>
        <button type="button" className="button primary" onClick={logout}>
          Déconnexion
        </button>
      </div>
    </header>
  );
};

export default Topbar;
