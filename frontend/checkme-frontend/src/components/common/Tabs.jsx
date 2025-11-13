import { useState } from 'react';
import PropTypes from 'prop-types';

const Tabs = ({ tabs, defaultActiveId }) => {
  const [activeTab, setActiveTab] = useState(defaultActiveId ?? tabs[0]?.id);

  const active = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <div className="tab-container">
      <div className="tab-list">
        {tabs.map((tab) => (
          <button
            type="button"
            key={tab.id}
            className={`tab ${tab.id === active?.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-panel">{active?.content}</div>
    </div>
  );
};

Tabs.propTypes = {
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      content: PropTypes.node.isRequired
    })
  ).isRequired,
  defaultActiveId: PropTypes.string
};

export default Tabs;
