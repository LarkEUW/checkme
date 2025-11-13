import PropTypes from 'prop-types';

const FullScreenLoader = ({ message = 'Chargement...' }) => (
  <div className="fullscreen-loader">
    <div className="spinner" />
    <p>{message}</p>
  </div>
);

FullScreenLoader.propTypes = {
  message: PropTypes.string
};

export default FullScreenLoader;
