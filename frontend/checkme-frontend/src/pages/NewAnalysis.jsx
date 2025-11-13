import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createAnalysisJob } from '../api/analysis.js';

const STEPS = [
  'Détection ou import de l’extension',
  'Création ou association de la fiche extension',
  'Gestion de la version et des métadonnées',
  'Extraction du manifest & pré-traitements',
  'Exécution parallèle des modules',
  'Calcul du score final (0 → 50)',
  'Génération du rapport JSON & PDF'
];

const NewAnalysis = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState('url');
  const [url, setUrl] = useState('');
  const [storeType, setStoreType] = useState('chrome');
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [lastJob, setLastJob] = useState(null);

  const isStoreMode = useMemo(() => mode === 'url' || mode === 'combined', [mode]);
  const isFileMode = useMemo(() => mode === 'file' || mode === 'combined', [mode]);

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault();
      setError(null);

      if (isStoreMode && !url) {
        setError('Veuillez fournir l’URL de la boutique.');
        return;
      }

      if (isFileMode && !file) {
        setError('Veuillez joindre un fichier .crx ou .xpi.');
        return;
      }

      setSubmitting(true);
      try {
        const result = await createAnalysisJob({
          mode,
          url,
          storeType: isStoreMode ? storeType : undefined,
          file
        });
        setLastJob(result);
      } catch (err) {
        setError(err.message || 'Impossible de lancer l’analyse.');
      } finally {
        setSubmitting(false);
      }
    },
    [mode, url, storeType, file, isStoreMode, isFileMode]
  );

  return (
    <div className="grid" style={{ gap: '32px' }}>
      <section className="page-header">
        <h2>Lancer une nouvelle analyse</h2>
        <p>
          Comparez les extensions Chrome, Edge et Firefox en choisissant la source de données la plus adaptée à votre mission.
        </p>
      </section>

      <section className="grid grid-cols-2">
        <form className="card form" onSubmit={handleSubmit}>
          <h3>Mode d’import</h3>
          <div className="form-group">
            <label>Type d’analyse</label>
            <div style={{ display: 'flex', gap: '12px' }}>
              {[
                { value: 'url', label: 'Store uniquement' },
                { value: 'file', label: 'Fichier local' },
                { value: 'combined', label: 'Fichier + Store' }
              ].map((option) => (
                <label key={option.value} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <input
                    type="radio"
                    name="mode"
                    value={option.value}
                    checked={mode === option.value}
                    onChange={(e) => setMode(e.target.value)}
                    required
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>

          {isStoreMode ? (
            <>
              <div className="form-group">
                <label htmlFor="storeType">Boutique</label>
                <select
                  id="storeType"
                  value={storeType}
                  onChange={(e) => setStoreType(e.target.value)}
                  required={isStoreMode}
                >
                  <option value="chrome">Chrome Web Store</option>
                  <option value="firefox">Mozilla Add-ons</option>
                  <option value="edge">Microsoft Edge Store</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="url">URL de l’extension</label>
                <input
                  id="url"
                  type="url"
                  placeholder="https://chrome.google.com/webstore/detail/.../id"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required={isStoreMode}
                />
              </div>
            </>
          ) : null}

          {isFileMode ? (
            <div className="form-group">
              <label htmlFor="file">Paquet .crx / .xpi</label>
              <input
                id="file"
                type="file"
                accept=".crx,.xpi,.zip"
                onChange={(event) => setFile(event.target.files[0] ?? null)}
                required={isFileMode}
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--color-muted)' }}>
                Le fichier est stocké de manière sécurisée le temps de l’analyse.
              </span>
            </div>
          ) : null}

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

          <button type="submit" className="button primary" disabled={submitting}>
            {submitting ? 'Analyse en cours...' : 'Démarrer l’analyse'}
          </button>
        </form>

        <div className="card">
          <h3>Pipeline CheckMe</h3>
          <ol style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingLeft: '20px' }}>
            {STEPS.map((step, index) => (
              <li key={step} style={{ color: 'var(--color-muted)' }}>
                <strong style={{ display: 'block', color: 'var(--color-text)' }}>
                  Étape {index + 1}
                </strong>
                {step}
              </li>
            ))}
          </ol>
          <div className="divider" style={{ margin: '24px 0' }} />
          <p style={{ margin: 0, color: 'var(--color-muted)', fontSize: '0.9rem' }}>
            Les modules désactivés (ex: Threat Intel sans clé API) recalculent automatiquement la pondération.
          </p>
        </div>
      </section>

      {lastJob ? (
        <section className="card">
          <h3>Analyse créée</h3>
          <p>
            Job <code>{lastJob.id}</code> initialisé avec succès. Statut actuel :{' '}
            <span className="badge needs-review">{lastJob.status}</span>
          </p>
          <div style={{ display: 'flex', gap: '16px' }}>
            <button type="button" className="button primary" onClick={() => navigate(`/reports/${lastJob.id}`)}>
              Ouvrir le rapport
            </button>
            <button type="button" className="button ghost" onClick={() => navigate('/reports')}>
              Voir l’historique
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
};

export default NewAnalysis;
