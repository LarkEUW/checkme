import PropTypes from 'prop-types';
import classNames from 'classnames';
import { getVerdictMeta } from '../../utils/verdict.js';

const ScoreGauge = ({ score, verdict }) => {
  const normalized = Math.min(Math.max(score, 0), 50);
  const percentage = (normalized / 50) * 100;
  const verdictInfo = getVerdictMeta(verdict);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
      <div
        style={{
          width: '140px',
          height: '140px',
          borderRadius: '50%',
          background: `conic-gradient(var(--color-primary) ${percentage * 3.6}deg, var(--color-border) ${percentage * 3.6}deg 360deg)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative'
        }}
      >
        <div
          style={{
            width: '104px',
            height: '104px',
            borderRadius: '50%',
            background: 'var(--color-surface)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
            boxShadow: 'inset 0 0 0 1px var(--color-border)'
          }}
        >
          <strong style={{ fontSize: '1.8rem' }}>{normalized.toFixed(1)}</strong>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-muted)' }}>sur 50</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <span className={classNames('badge', verdictInfo.className)}>{verdictInfo.label}</span>
        <p style={{ margin: 0, color: 'var(--color-muted)' }}>
          Score agrégé basé sur la pondération dynamique des modules actifs.
        </p>
      </div>
    </div>
  );
};

ScoreGauge.propTypes = {
  score: PropTypes.number.isRequired,
  verdict: PropTypes.string
};

export default ScoreGauge;
