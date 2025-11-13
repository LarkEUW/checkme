import { useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import StatCard from '../components/common/StatCard.jsx';
import ScoreGauge from '../components/common/ScoreGauge.jsx';
import Tabs from '../components/common/Tabs.jsx';
import { getMetrics } from '../api/settings.js';
import { listAnalyses } from '../api/analysis.js';
import { getVerdictMeta } from '../utils/verdict.js';
import { sampleMetrics, sampleAnalyses } from '../utils/mocks.js';

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setError(null);
      try {
        const [metricResponse, analysesResponse] = await Promise.all([
          getMetrics().catch(() => null),
          listAnalyses({ limit: 10 })
        ]);
        setMetrics(metricResponse ?? sampleMetrics);
        setAnalyses(analysesResponse?.length ? analysesResponse : sampleAnalyses);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const recentCompleted = useMemo(
    () => analyses.filter((analysis) => analysis.status === 'completed'),
    [analyses]
  );

  const averageScore = useMemo(() => {
    if (!recentCompleted.length) return 0;
    const total = recentCompleted.reduce((acc, analysis) => acc + (analysis.final_score ?? 0), 0);
    return Math.round((total / recentCompleted.length) * 10) / 10;
  }, [recentCompleted]);

  const verdictBreakdown = useMemo(() => {
    const counts = { safe: 0, needs_review: 0, high_risk: 0, block: 0 };
    recentCompleted.forEach((analysis) => {
      if (!analysis.verdict) return;
      counts[analysis.verdict] = (counts[analysis.verdict] || 0) + 1;
    });
    const total = Object.values(counts).reduce((acc, val) => acc + val, 0) || 1;
    return Object.entries(counts).map(([key, value]) => {
      const meta = getVerdictMeta(key);
      return {
        key,
        label: meta.label,
        badge: meta.className,
        value,
        percentage: Math.round((value / total) * 100)
      };
    });
  }, [recentCompleted]);

  if (loading) {
    return (
      <div className="card" data-variant="flat">
        Chargement des métriques...
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" data-variant="flat" style={{ color: 'var(--color-danger)' }}>
        Impossible de charger le tableau de bord : {error}
      </div>
    );
  }

  return (
    <div className="grid" style={{ gap: '24px' }}>
      <section className="page-header">
        <h2>Suivi en temps réel</h2>
        <p>Vue consolidée des analyses d’extensions et des indicateurs de posture de sécurité.</p>
      </section>

      <section className="grid grid-cols-3">
        <StatCard
          title="Analyses totales"
          value={metrics?.analyses?.total ?? analyses.length}
          trendLabel="+12% vs. 30 derniers jours"
          trendDirection="up"
          icon="🧪"
        />
        <StatCard
          title="Analyses complétées"
          value={metrics?.analyses?.completed ?? recentCompleted.length}
          trendLabel="98% de réussite"
          trendDirection="up"
          icon="✅"
        />
        <StatCard
          title="Extensions suivies"
          value={metrics?.analyses?.total ? metrics.analyses.total : analyses.length}
          trendLabel="17 nouvelles cette semaine"
          trendDirection="neutral"
          icon="🧩"
        />
      </section>

      <section className="grid grid-cols-2">
        <div className="card">
          <h3>Score de confiance moyen</h3>
          <ScoreGauge score={averageScore} verdict="needs_review" />
        </div>

        <div className="card">
          <h3>Répartition des verdicts</h3>
          <ul className="list">
              {verdictBreakdown.map((item) => (
                <li key={item.key} className="list-item">
                <div>
                  <strong>{item.label}</strong>
                  <p style={{ margin: '8px 0 0', color: 'var(--color-muted)' }}>
                    {item.percentage}% des rapports complétés
                  </p>
                </div>
                  <span className={`badge ${item.badge}`}>{item.value}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="card">
        <h3>Dernières analyses</h3>
        {analyses.length === 0 ? (
          <div className="empty-state">Aucune analyse pour le moment.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Statut</th>
                <th>Score final</th>
                <th>Verdict</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {analyses.slice(0, 8).map((analysis) => (
                <tr key={analysis.id}>
                  <td>{analysis.id.slice(0, 8)}</td>
                  <td>
                    <span className="badge needs-review">{analysis.status}</span>
                  </td>
                  <td>{analysis.final_score ?? '—'}</td>
                  <td>{analysis.verdict ?? '—'}</td>
                  <td>{format(new Date(analysis.created_at), 'dd/MM/yyyy HH:mm')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h3>Flux en attente</h3>
        <Tabs
          tabs={[
            {
              id: 'pending',
              label: 'À valider',
              content: (
                <ul className="list">
                  {analyses
                    .filter((analysis) => analysis.status !== 'completed')
                    .slice(0, 5)
                    .map((analysis) => (
                      <li key={analysis.id} className="list-item">
                        <div>
                          <strong>{analysis.id.slice(0, 10)}</strong>
                          <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                            Créé le {new Date(analysis.created_at).toLocaleString()}
                          </p>
                        </div>
                        <span className="badge high-risk">{analysis.status}</span>
                      </li>
                    ))}
                  {analyses.filter((analysis) => analysis.status !== 'completed').length === 0 ? (
                    <div className="empty-state">Aucun job en attente.</div>
                  ) : null}
                </ul>
              )
            },
            {
              id: 'actions',
              label: 'Actions recommandées',
              content: (
                <ul className="list">
                  <li className="list-item">
                    <div>
                      <strong>Mettre à jour la matrice de permissions</strong>
                      <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                        Assurez-vous que les nouvelles permissions critiques détectées sont bien catégorisées.
                      </p>
                    </div>
                    <span className="badge needs-review">Hebdomadaire</span>
                  </li>
                  <li className="list-item">
                    <div>
                      <strong>Importer les clés API Threat Intel</strong>
                      <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                        Activez VirusTotal et AbuseIPDB pour enrichir les verdicts automatiques.
                      </p>
                    </div>
                    <span className="badge high-risk">Priorité</span>
                  </li>
                </ul>
              )
            }
          ]}
        />
      </section>
    </div>
  );
};

export default Dashboard;
