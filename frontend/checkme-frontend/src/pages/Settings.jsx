import { useCallback, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import {
  createApiKey,
  createSetting,
  deleteApiKey,
  deleteSetting,
  listApiKeys,
  listSettings,
  toggleApiKey,
  upsertSetting
} from '../api/settings.js';
import { useAuth } from '../context/AuthContext.jsx';

const Settings = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [newSettingKey, setNewSettingKey] = useState('');
  const [newSettingValue, setNewSettingValue] = useState('{\n  \n}');
  const [newSettingDescription, setNewSettingDescription] = useState('');

  const [newApiKey, setNewApiKey] = useState({
    service_name: '',
    key_name: '',
    encrypted_key: ''
  });

  const canEdit = useMemo(() => user?.role === 'admin', [user]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [settingsResponse, apiKeysResponse] = await Promise.all([listSettings(), listApiKeys()]);
      setSettings(settingsResponse);
      setApiKeys(apiKeysResponse);
    } catch (err) {
      setError(err.message || 'Impossible de récupérer les paramètres.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSettingSave = async (setting) => {
    if (!canEdit) return;
    try {
      const parsed = JSON.parse(setting.valueDraft);
      await upsertSetting(setting.key, {
        key: setting.key,
        value: parsed,
        description: setting.description
      });
      await refresh();
    } catch (err) {
      setError(err.message || 'Paramètre non enregistré. Vérifiez le JSON.');
    }
  };

  const handleSettingDelete = async (key) => {
    if (!canEdit || !window.confirm('Supprimer ce paramètre ?')) return;
    await deleteSetting(key);
    await refresh();
  };

  const handleNewSetting = async (event) => {
    event.preventDefault();
    if (!canEdit) return;
    try {
      const value = JSON.parse(newSettingValue);
      await createSetting({
        key: newSettingKey,
        value,
        description: newSettingDescription || undefined
      });
      setNewSettingKey('');
      setNewSettingValue('{\n  \n}');
      setNewSettingDescription('');
      await refresh();
    } catch (err) {
      setError(err.message || 'Nouveau paramètre invalide.');
    }
  };

  const handleNewApiKey = async (event) => {
    event.preventDefault();
    if (!canEdit) return;
    try {
      await createApiKey(newApiKey);
      setNewApiKey({ service_name: '', key_name: '', encrypted_key: '' });
      await refresh();
    } catch (err) {
      setError(err.message || 'Impossible de créer la clé API.');
    }
  };

  return (
    <div className="grid" style={{ gap: '24px' }}>
      <section className="page-header">
        <h2>Centre de configuration</h2>
        <p>
          Gérez les poids de scoring, les modules activés et les intégrations tierces (Threat Intel, IA).
        </p>
      </section>

      {error ? (
        <section className="card" data-variant="flat" style={{ color: 'var(--color-danger)' }}>
          {error}
        </section>
      ) : null}

      {loading ? (
        <section className="card" data-variant="flat">
          Chargement...
        </section>
      ) : (
        <>
          <section className="card">
            <h3>Paramètres structurés</h3>
            {settings.length === 0 ? (
              <div className="empty-state">Aucun paramètre défini.</div>
            ) : (
              <div className="grid" style={{ gap: '16px' }}>
                {settings.map((setting) => (
                  <SettingEditor
                    key={setting.id}
                    setting={setting}
                    canEdit={canEdit}
                    onSave={handleSettingSave}
                    onDelete={handleSettingDelete}
                  />
                ))}
              </div>
            )}
            {canEdit ? (
              <form className="form" onSubmit={handleNewSetting} style={{ marginTop: '24px' }}>
                <h4>Ajouter un paramètre</h4>
                <div className="form-group">
                  <label htmlFor="setting-key">Clé</label>
                  <input
                    id="setting-key"
                    value={newSettingKey}
                    onChange={(e) => setNewSettingKey(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="setting-desc">Description</label>
                  <input
                    id="setting-desc"
                    value={newSettingDescription}
                    onChange={(e) => setNewSettingDescription(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="setting-value">Valeur JSON</label>
                  <textarea
                    id="setting-value"
                    rows={6}
                    value={newSettingValue}
                    onChange={(e) => setNewSettingValue(e.target.value)}
                  />
                </div>
                <button type="submit" className="button primary">
                  Enregistrer
                </button>
              </form>
            ) : (
              <p style={{ marginTop: '16px', color: 'var(--color-muted)' }}>
                Les paramètres sont en lecture seule pour les utilisateurs non administrateurs.
              </p>
            )}
          </section>

          <section className="card">
            <h3>Clés API & intégrations</h3>
            {apiKeys.length === 0 ? (
              <div className="empty-state">Aucune clé API renseignée pour le moment.</div>
            ) : (
              <ul className="list">
                {apiKeys.map((key) => (
                  <li key={key.id} className="list-item">
                    <div>
                      <strong>
                        {key.service_name} • {key.key_name}
                      </strong>
                      <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>
                        Utilisation : {key.usage_count} • Dernier usage :{' '}
                        {key.last_used ? new Date(key.last_used).toLocaleString() : '—'}
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span className={`badge ${key.is_active ? 'safe' : 'high-risk'}`}>
                        {key.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {canEdit ? (
                        <>
                          <button
                            type="button"
                            className="button ghost"
                            onClick={async () => {
                              await toggleApiKey(key.id);
                              await refresh();
                            }}
                          >
                            Basculer
                          </button>
                          <button
                            type="button"
                            className="button primary"
                            onClick={async () => {
                              if (window.confirm('Supprimer cette clé API ?')) {
                                await deleteApiKey(key.id);
                                await refresh();
                              }
                            }}
                          >
                            Supprimer
                          </button>
                        </>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            )}
            {canEdit ? (
              <form className="form" onSubmit={handleNewApiKey} style={{ marginTop: '24px' }}>
                <h4>Enregistrer une clé</h4>
                <div className="form-group">
                  <label htmlFor="api-service">Service</label>
                  <input
                    id="api-service"
                    value={newApiKey.service_name}
                    onChange={(e) =>
                      setNewApiKey((prev) => ({ ...prev, service_name: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="api-name">Nom de la clé</label>
                  <input
                    id="api-name"
                    value={newApiKey.key_name}
                    onChange={(e) =>
                      setNewApiKey((prev) => ({ ...prev, key_name: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="api-encrypted">Clé chiffrée</label>
                  <input
                    id="api-encrypted"
                    value={newApiKey.encrypted_key}
                    onChange={(e) =>
                      setNewApiKey((prev) => ({ ...prev, encrypted_key: e.target.value }))
                    }
                    required
                  />
                </div>
                <button type="submit" className="button primary">
                  Ajouter
                </button>
              </form>
            ) : null}
          </section>
        </>
      )}
    </div>
  );
};

const SettingEditor = ({ setting, canEdit, onSave, onDelete }) => {
  const [draft, setDraft] = useState(JSON.stringify(setting.value, null, 2));

  return (
    <div className="card" data-variant="flat">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <strong>{setting.key}</strong>
          <p style={{ margin: '4px 0 0', color: 'var(--color-muted)' }}>{setting.description}</p>
        </div>
        <span className="badge needs-review">ID: {setting.id.slice(0, 8)}</span>
      </div>
      <div className="form-group" style={{ marginTop: '16px' }}>
        <label>Valeur JSON</label>
        <textarea
          rows={6}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={!canEdit}
        />
      </div>
      {canEdit ? (
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="button"
            className="button primary"
            onClick={() => onSave({ ...setting, valueDraft: draft })}
          >
            Sauvegarder
          </button>
          <button type="button" className="button ghost" onClick={() => onDelete(setting.key)}>
            Supprimer
          </button>
        </div>
      ) : null}
    </div>
  );
};

SettingEditor.propTypes = {
  setting: PropTypes.shape({
    id: PropTypes.string.isRequired,
    key: PropTypes.string.isRequired,
    value: PropTypes.any,
    description: PropTypes.string
  }).isRequired,
  canEdit: PropTypes.bool.isRequired,
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired
};

export default Settings;
