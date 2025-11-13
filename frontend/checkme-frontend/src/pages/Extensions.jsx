import { useEffect, useMemo, useState } from 'react';
import { listExtensions } from '../api/extensions.js';

const storeOptions = [
  { value: '', label: 'Toutes les boutiques' },
  { value: 'chrome', label: 'Chrome' },
  { value: 'firefox', label: 'Firefox' },
  { value: 'edge', label: 'Edge' }
];

const Extensions = () => {
  const [storeType, setStoreType] = useState('');
  const [query, setQuery] = useState('');
  const [extensions, setExtensions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchExtensions = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await listExtensions(
          storeType ? { store_type: storeType } : undefined
        );
        setExtensions(response);
      } catch (err) {
        setError(err.message || 'Impossible de récupérer les extensions.');
      } finally {
        setLoading(false);
      }
    };
    fetchExtensions();
  }, [storeType]);

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase();
    if (!search) return extensions;
    return extensions.filter((extension) =>
      [extension.name, extension.store_id, extension.developer_name]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(search))
    );
  }, [extensions, query]);

  return (
    <div className="grid" style={{ gap: '24px' }}>
      <section className="page-header">
        <h2>Catalogue des extensions</h2>
        <p>
          Retrouvez les extensions analysées, leur boutique d’origine et les informations de l’éditeur.
        </p>
      </section>

      <section className="card" data-variant="flat">
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ minWidth: '220px' }}>
            <label htmlFor="store">Boutique</label>
            <select id="store" value={storeType} onChange={(e) => setStoreType(e.target.value)}>
              {storeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ flex: '1' }}>
            <label htmlFor="search">Recherche</label>
            <input
              id="search"
              type="search"
              placeholder="Nom, ID de store, éditeur..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
      </section>

      <section className="card">
        <h3>Extensions suivies</h3>
        {loading ? (
          <div className="empty-state">Chargement...</div>
        ) : error ? (
          <div className="empty-state" style={{ color: 'var(--color-danger)' }}>
            {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">Aucune extension ne correspond aux critères.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>ID Store</th>
                <th>Boutique</th>
                <th>Éditeur</th>
                <th>Vérifié</th>
                <th>Créé le</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((extension) => (
                <tr key={extension.id}>
                  <td>{extension.name}</td>
                  <td>{extension.store_id}</td>
                  <td>{extension.store_type}</td>
                  <td>{extension.developer_name ?? '—'}</td>
                  <td>{extension.verified_publisher ? 'Oui' : 'Non'}</td>
                  <td>{new Date(extension.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default Extensions;
