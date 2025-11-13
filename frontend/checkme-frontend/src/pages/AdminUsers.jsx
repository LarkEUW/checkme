import { useCallback, useEffect, useMemo, useState } from 'react';
import { listUsers, updateUser, deleteUser } from '../api/users.js';
import { useAuth } from '../context/AuthContext.jsx';

const AdminUsers = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const canManage = useMemo(() => user?.role === 'admin', [user]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listUsers({ limit: 100 });
      setUsers(response);
    } catch (err) {
      setError(err.message || 'Impossible de récupérer les utilisateurs.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canManage) {
      refresh();
    }
  }, [refresh, canManage]);

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase();
    if (!search) return users;
    return users.filter((item) =>
      [item.email, item.full_name, item.role].some((field) =>
        field.toLowerCase().includes(search)
      )
    );
  }, [users, query]);

  const handleUpdate = async (userId, attrs) => {
    try {
      const updated = await updateUser(userId, attrs);
      setUsers((prev) => prev.map((item) => (item.id === userId ? updated : item)));
    } catch (err) {
      setError(err.message || 'Mise à jour impossible.');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Supprimer cet utilisateur ?')) return;
    await deleteUser(userId);
    await refresh();
  };

  if (!canManage) {
    return (
      <section className="card" data-variant="flat">
        Vous devez être administrateur pour gérer les utilisateurs.
      </section>
    );
  }

  return (
    <div className="grid" style={{ gap: '24px' }}>
      <section className="page-header">
        <h2>Administration des utilisateurs</h2>
        <p>Activez, désactivez ou promouvez des membres de l’équipe SOC.</p>
      </section>

      <section className="card" data-variant="flat">
        <div className="form-group" style={{ maxWidth: '360px' }}>
          <label htmlFor="admin-search">Recherche</label>
          <input
            id="admin-search"
            type="search"
            placeholder="Nom, e-mail, rôle..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </section>

      <section className="card">
        <h3>Collaborateurs</h3>
        {loading ? (
          <div className="empty-state">Chargement...</div>
        ) : error ? (
          <div className="empty-state" style={{ color: 'var(--color-danger)' }}>
            {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">Aucun utilisateur.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Email</th>
                <th>Rôle</th>
                <th>Statut</th>
                <th>Créé le</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td>{item.full_name}</td>
                  <td>{item.email}</td>
                  <td>
                    <select
                      value={item.role}
                      onChange={(e) => handleUpdate(item.id, { role: e.target.value })}
                    >
                      <option value="user">Utilisateur</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="button ghost"
                      onClick={() => handleUpdate(item.id, { is_active: !item.is_active })}
                    >
                      {item.is_active ? 'Actif' : 'Inactif'}
                    </button>
                  </td>
                  <td>{new Date(item.created_at).toLocaleDateString()}</td>
                  <td>
                    <button type="button" className="button primary" onClick={() => handleDelete(item.id)}>
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default AdminUsers;
