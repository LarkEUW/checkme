import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ScoreGauge from '../components/common/ScoreGauge.jsx';
import Tabs from '../components/common/Tabs.jsx';
import { getAnalysis, deleteAnalysis } from '../api/analysis.js';
import { addComment, addDecision, getComments, getDecisions } from '../api/reports.js';
import { useAuth } from '../context/AuthContext.jsx';

const ReportDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [analysis, setAnalysis] = useState(null);
  const [comments, setComments] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [decisionForm, setDecisionForm] = useState({ decision: 'accept', reason: '' });
  const [submitting, setSubmitting] = useState(false);

  const refreshData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [analysisResponse, commentResponse, decisionResponse] = await Promise.all([
        getAnalysis(id),
        getComments(id),
        getDecisions(id).catch(() => [])
      ]);
      setAnalysis(analysisResponse);
      setComments(commentResponse);
      setDecisions(decisionResponse);
    } catch (err) {
      setError(err.message || 'Impossible de récupérer le rapport.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const handleCommentSubmit = useCallback(
    async (event) => {
      event.preventDefault();
      if (!commentText.trim()) return;
      setSubmitting(true);
      try {
        await addComment(id, commentText.trim());
        setCommentText('');
        const refreshed = await getComments(id);
        setComments(refreshed);
      } catch (err) {
        setError(err.message || 'Commentaire impossible à enregistrer.');
      } finally {
        setSubmitting(false);
      }
    },
    [commentText, id]
  );

  const handleDecisionSubmit = useCallback(
    async (event) => {
      event.preventDefault();
      setSubmitting(true);
      try {
        await addDecision(id, decisionForm);
        const refreshed = await getDecisions(id);
        setDecisions(refreshed);
        setDecisionForm({ decision: 'accept', reason: '' });
      } catch (err) {
        setError(err.message || 'Décision non enregistrée.');
      } finally {
        setSubmitting(false);
      }
    },
    [decisionForm, id]
  );

  const handleDelete = useCallback(async () => {
    if (!window.confirm('Supprimer définitivement ce rapport ?')) return;
    await deleteAnalysis(id);
    navigate('/reports');
  }, [id, navigate]);

  const metadata = useMemo(() => analysis?.results?.metadata?.data ?? {}, [analysis]);
  const permissions = useMemo(() => analysis?.results?.permissions?.data ?? {}, [analysis]);
  const codeBehavior = useMemo(() => analysis?.results?.code_behavior ?? {}, [analysis]);
  const network = useMemo(() => analysis?.results?.network?.data ?? {}, [analysis]);
  const cve = useMemo(() => analysis?.results?.cve?.data ?? {}, [analysis]);
  const ai = useMemo(() => analysis?.results?.ai?.data ?? {}, [analysis]);

  if (loading) {
    return (
      <div className="card" data-variant="flat">
        Chargement du rapport...
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" data-variant="flat" style={{ color: 'var(--color-danger)' }}>
        {error}
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="card" data-variant="flat">
        Rapport introuvable.
      </div>
    );
  }

  const tabs = [
    {
      id: 'overview',
      label: 'Vue d’ensemble',
      content: (
        <div className="grid grid-cols-2">
          <div>
            <h4>Score & verdict</h4>
            <ScoreGauge score={analysis.final_score ?? 0} verdict={analysis.verdict} />
              <div style={{ marginTop: '16px' }}>
              <h4>Bonifications / Malus</h4>
              <ul>
                  {Object.entries(analysis.bonuses ?? {}).map(([key, value]) => (
                  <li key={key} style={{ color: 'var(--color-success)' }}>
                    +{value} {key}
                  </li>
                  ))}
                  {Object.entries(analysis.maluses ?? {}).map(([key, value]) => (
                  <li key={key} style={{ color: 'var(--color-danger)' }}>
                    {value} {key}
                  </li>
                  ))}
                  {Object.keys(analysis.bonuses ?? {}).length === 0 &&
                    Object.keys(analysis.maluses ?? {}).length === 0 && <li>Aucun ajustement.</li>}
              </ul>
            </div>
          </div>
          <div>
            <h4>Module scores</h4>
            <ul className="list">
              {Object.entries(analysis.scores ?? {}).map(([module, score]) => (
                <li key={module} className="list-item">
                  <div>
                    <strong>{module.replace('_', ' ')}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                      Score normalisé (0-10)
                    </p>
                  </div>
                  <span className="badge needs-review">{score?.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'permissions',
      label: 'Permissions',
      content: (
        <div className="grid grid-cols-2">
          <div>
            <h4>Permissions principales</h4>
            <ul>
              {(permissions.permissions ?? []).map((perm) => (
                <li key={perm}>{perm}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Permissions d’hôtes</h4>
            <ul>
              {(permissions.host_permissions ?? []).map((perm) => (
                <li key={perm}>{perm}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Distribution du risque</h4>
            <ul>
              {Object.entries(permissions.risk_distribution ?? {}).map(([risk, count]) => (
                <li key={risk}>
                  {risk} : <strong>{count}</strong>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'code',
      label: 'Comportements code',
      content: (
        <div>
          <h4>Patterns détectés</h4>
          {(codeBehavior.findings ?? []).length === 0 ? (
            <div className="empty-state">No suspicious pattern detected.</div>
          ) : (
            <ul className="list">
              {(codeBehavior.findings ?? []).map((finding, index) => (
                <li key={`${finding.message}-${index}`} className="list-item">
                  <div>
                    <strong>{finding.message}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                      Catégorie : {finding.category} • Fichier : {finding.file}
                    </p>
                  </div>
                  <span className="badge high-risk">{finding.severity}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )
    },
    {
      id: 'network',
      label: 'Réseau & privacy',
      content: (
        <div className="grid grid-cols-2">
          <div>
            <h4>Statistiques</h4>
            <ul>
              <li>Total URLs : {network.total_urls ?? 0}</li>
              <li>URLs externes : {network.external_urls ?? 0}</li>
              <li>HTTP non sécurisés : {network.http_urls ?? 0}</li>
              <li>Domaines uniques : {network.unique_domains ?? 0}</li>
              <li>Domaines de tracking : {network.tracking_domains ?? 0}</li>
            </ul>
          </div>
          <div>
            <h4>Domaines observés</h4>
            <ul>
              {(network.domains ?? []).map((domain) => (
                <li key={domain}>{domain}</li>
              ))}
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'cve',
      label: 'CVE & dépendances',
      content: (
        <div>
          <h4>Bibliothèques détectées</h4>
          <ul className="list">
            {(cve.libraries_found ?? []).map((lib) => (
              <li key={`${lib.name}-${lib.version}`} className="list-item">
                <div>
                  <strong>{lib.name}</strong>
                  <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                    Version {lib.version} • {lib.file}
                  </p>
                </div>
              </li>
            ))}
          </ul>
          <div className="divider" style={{ margin: '16px 0' }} />
          <h4>Vulnérabilités</h4>
          {(cve.cves ?? []).length === 0 ? (
            <div className="empty-state">Aucun CVE signalé.</div>
          ) : (
            <ul className="list">
              {cve.cves.map((cveItem) => (
                <li key={cveItem.id} className="list-item">
                  <div>
                    <strong>{cveItem.id}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                      {cveItem.library} {cveItem.version} • {cveItem.description}
                    </p>
                  </div>
                  <span className="badge high-risk">{cveItem.severity}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )
    },
    {
      id: 'ai',
      label: 'Analyse IA',
      content: (
        <div className="grid">
          <div>
            <h4>Résumé</h4>
            <p>{ai.summary ?? 'Analyse IA non disponible.'}</p>
          </div>
          <div>
            <h4>Scénarios d’attaque</h4>
            <ul className="list">
              {(ai.attack_scenarios ?? []).map((scenario) => (
                <li key={scenario.title} className="list-item">
                  <div>
                    <strong>{scenario.title}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                      {scenario.description}
                    </p>
                  </div>
                  <span className="badge needs-review">
                    {scenario.likelihood} / Impact {scenario.impact}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Recommandations</h4>
            <ul>
              {(ai.recommendations ?? []).map((recommendation) => (
                <li key={recommendation}>{recommendation}</li>
              ))}
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'collaboration',
      label: 'Collaboration',
      content: (
        <div className="grid grid-cols-2">
          <div>
            <h4>Commentaires</h4>
            <ul className="list">
              {comments.map((comment) => (
                <li key={comment.id} className="list-item">
                  <div>
                    <strong>{comment.user_name}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                      {new Date(comment.created_at).toLocaleString()}
                    </p>
                    <p>{comment.content}</p>
                  </div>
                </li>
              ))}
              {comments.length === 0 ? <div className="empty-state">Pas encore de commentaires.</div> : null}
            </ul>
            <form className="form" onSubmit={handleCommentSubmit} style={{ marginTop: '16px' }}>
              <div className="form-group">
                <label htmlFor="comment">Ajouter un commentaire</label>
                <textarea
                  id="comment"
                  rows={3}
                  placeholder="Partagez votre analyse ou un plan d’action..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                />
              </div>
              <button type="submit" className="button primary" disabled={submitting}>
                Publier
              </button>
            </form>
          </div>

          <div>
            <h4>Décisions</h4>
            <ul className="list">
              {decisions.map((decision) => (
                <li key={decision.id} className="list-item">
                  <div>
                    <strong>{decision.user_name}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                      {new Date(decision.created_at).toLocaleString()}
                    </p>
                    <p>{decision.reason ?? '—'}</p>
                  </div>
                  <span className="badge needs-review">{decision.decision}</span>
                </li>
              ))}
              {decisions.length === 0 ? <div className="empty-state">Pas encore de décision.</div> : null}
            </ul>
            {user?.role === 'admin' ? (
              <form className="form" onSubmit={handleDecisionSubmit} style={{ marginTop: '16px' }}>
                <div className="form-group">
                  <label htmlFor="decision">Prendre une décision</label>
                  <select
                    id="decision"
                    value={decisionForm.decision}
                    onChange={(e) =>
                      setDecisionForm((prev) => ({
                        ...prev,
                        decision: e.target.value
                      }))
                    }
                  >
                    <option value="accept">Accept</option>
                    <option value="reject">Reject</option>
                    <option value="pending">Pending</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="reason">Justification</label>
                  <textarea
                    id="reason"
                    rows={3}
                    value={decisionForm.reason}
                    onChange={(e) =>
                      setDecisionForm((prev) => ({
                        ...prev,
                        reason: e.target.value
                      }))
                    }
                    placeholder="Expliquez pourquoi l’extension est autorisée, bloquée ou en attente."
                  />
                </div>
                <button type="submit" className="button primary" disabled={submitting}>
                  Valider
                </button>
              </form>
            ) : (
              <p style={{ color: 'var(--color-muted)', fontSize: '0.85rem' }}>
                Seuls les administrateurs peuvent enregistrer une décision.
              </p>
            )}
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="grid" style={{ gap: '24px' }}>
      <section className="page-header">
        <h2>Rapport : {metadata.name ?? analysis.id}</h2>
        <p>
          Version analysée : {metadata.version ?? 'inconnue'} • Généré le{' '}
          {analysis.completed_at ? new Date(analysis.completed_at).toLocaleString() : 'En cours'}
        </p>
      </section>

      <section className="card" data-variant="flat">
        <div style={{ display: 'flex', gap: '12px' }}>
          <button type="button" className="button ghost" onClick={() => navigate('/reports')}>
            ◀ Retour à la liste
          </button>
          <button type="button" className="button ghost" onClick={() => window.print()}>
            📄 Exporter en PDF
          </button>
          <button
            type="button"
            className="button ghost"
            onClick={() => navigator.clipboard.writeText(JSON.stringify(analysis, null, 2))}
          >
            ⎘ Copier JSON
          </button>
          {user?.role === 'admin' ? (
            <button type="button" className="button primary" onClick={handleDelete}>
              Supprimer
            </button>
          ) : null}
        </div>
      </section>

      <section className="card">
        <Tabs tabs={tabs} />
      </section>
    </div>
  );
};

export default ReportDetail;
