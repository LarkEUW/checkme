import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listAnalyses } from '../api/analysis.js';
import { formatVerdictLabel, getVerdictMeta } from '../utils/verdict.js';

const statusOptions = [
  { value: '', label: 'Tous les statuts' },
  { value: 'pending', label: 'En attente' },
  { value: 'in_progress', label: 'En cours' },
  { value: 'completed', label: 'Terminé' },
  { value: 'failed', label: 'Échec' }
];

const verdictOptions = [
  { value: '', label: 'Tous les verdicts' },
  { value: 'safe', label: 'Safe' },
  { value: 'needs_review', label: 'Needs review' },
  { value: 'high_risk', label: 'High risk' },
  { value: 'block', label: 'Block / Malicious' }
];

const ReportsList = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [verdict, setVerdict] = useState('');
  const [query, setQuery] = useState('');
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalyses = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await listAnalyses({
          status: status || undefined,
          verdict: verdict || undefined
        });
        setAnalyses(response);
      } catch (err) {
        setError(err.message || 'Impossible de récupérer les analyses.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalyses();
  }, [status, verdict]);

  const filteredAnalyses = useMemo(() => {
    const search = query.trim().toLowerCase();
    if (!search) return analyses;
    return analyses.filter(
      (analysis) =>
        analysis.id.toLowerCase().includes(search) ||
        (analysis.verdict ?? '').toLowerCase().includes(search)
    );
  }, [analyses, query]);

  return (
    <div className="grid" style={{ gap: '24px' }}>
      <section className="page-header">
        <h2>Rapports d’analyse</h2>
        <p>
          Filtrez les rapports générés par statut opérationnel, verdict ou recherche textuelle. Exportez les résultats au format JSON/PDF.
        </p>
      </section>

      <section className="card" data-variant="flat">
        <div
          style={{
            display: 'flex',
            gap: '16px',
            flexWrap: 'wrap'
          }}
        >
          <div className="form-group" style={{ minWidth: '220px', flex: '1' }}>
            <label htmlFor="status">Statut</label>
            <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ minWidth: '220px', flex: '1' }}>
            <label htmlFor="verdict">Verdict</label>
            <select id="verdict" value={verdict} onChange={(e) => setVerdict(e.target.value)}>
              {verdictOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ flex: '2' }}>
            <label htmlFor="query">Recherche</label>
            <input
              id="query"
              type="search"
              placeholder="Rechercher par ID, verdict..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
      </section>

      <section className="card">
        <h3>Historique complet</h3>
        {loading ? (
          <div className="empty-state">Chargement...</div>
        ) : error ? (
          <div className="empty-state" style={{ color: 'var(--color-danger)' }}>
            {error}
          </div>
        ) : filteredAnalyses.length === 0 ? (
          <div className="empty-state">Aucun rapport ne correspond aux filtres.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Statut</th>
                <th>Score</th>
                <th>Verdict</th>
                <th>Date</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filteredAnalyses.map((analysis) => (
                <tr key={analysis.id}>
                  <td>{analysis.id}</td>
                  <td>
                    <span className="badge needs-review">{analysis.status}</span>
                  </td>
                  <td>{analysis.final_score ?? '—'}</td>
                  <td>
                    {analysis.verdict ? (
                      <span className={`badge ${getVerdictMeta(analysis.verdict).className}`}>
                        {formatVerdictLabel(analysis.verdict)}
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>{new Date(analysis.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      type="button"
                      className="button ghost"
                      onClick={() => navigate(`/reports/${analysis.id}`)}
                    >
                      Ouvrir
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

export default ReportsList;
