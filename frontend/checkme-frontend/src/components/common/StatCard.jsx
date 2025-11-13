import PropTypes from 'prop-types';
import classNames from 'classnames';

const StatCard = ({ title, value, trendLabel, trendDirection = 'neutral', icon }) => {
  return (
    <div className="card stat-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3>{title}</h3>
        {icon ? <span aria-hidden="true">{icon}</span> : null}
      </div>
      <strong>{value}</strong>
      {trendLabel ? (
        <span className={classNames('stat-trend', { positive: trendDirection === 'up', negative: trendDirection === 'down' })}>
          {trendLabel}
        </span>
      ) : null}
    </div>
  );
};

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  trendLabel: PropTypes.string,
  trendDirection: PropTypes.oneOf(['up', 'down', 'neutral']),
  icon: PropTypes.node
};

export default StatCard;
