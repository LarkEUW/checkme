import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import Topbar from './Topbar.jsx';

const AppLayout = () => {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-view">
        <Topbar />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
