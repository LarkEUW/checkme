import { useCallback, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault();
      setError(null);
      setLoading(true);
      try {
        await login(email, password);
        const redirectTo = location.state?.from?.pathname || '/';
        navigate(redirectTo, { replace: true });
      } catch (err) {
        setError(err.message || 'Échec de l’authentification');
      } finally {
        setLoading(false);
      }
    },
    [email, password, login, navigate, location.state]
  );

  return (
    <div className="login-screen">
      <div className="login-card">
        <div>
          <h1>Bienvenue sur CheckMe</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
            Analysez, priorisez et validez la sécurité des extensions navigateur.
          </p>
        </div>

        <form className="form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Adresse e-mail professionnelle</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="analyste@soc.example"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error ? (
            <div
              style={{
                padding: '12px',
                borderRadius: '12px',
                background: 'rgba(239,68,68,0.12)',
                color: 'var(--color-danger)',
                fontSize: '0.9rem'
              }}
            >
              {error}
            </div>
          ) : null}
          <button type="submit" className="button primary" disabled={loading}>
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="divider" />
        <p style={{ fontSize: '0.85rem', color: 'var(--color-muted)', margin: 0 }}>
          Besoin d’un accès ? Contactez votre administrateur CheckMe.
        </p>
      </div>
    </div>
  );
};

export default Login;
