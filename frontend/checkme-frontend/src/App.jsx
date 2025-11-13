import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/auth/ProtectedRoute.jsx';
import AppLayout from './components/layout/AppLayout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import NewAnalysis from './pages/NewAnalysis.jsx';
import ReportsList from './pages/ReportsList.jsx';
import ReportDetail from './pages/ReportDetail.jsx';
import Extensions from './pages/Extensions.jsx';
import Settings from './pages/Settings.jsx';
import AdminUsers from './pages/AdminUsers.jsx';
import Login from './pages/auth/Login.jsx';

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="/analysis/new" element={<NewAnalysis />} />
        <Route path="/reports" element={<ReportsList />} />
        <Route path="/reports/:id" element={<ReportDetail />} />
        <Route path="/extensions" element={<Extensions />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/admin/users" element={<AdminUsers />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
