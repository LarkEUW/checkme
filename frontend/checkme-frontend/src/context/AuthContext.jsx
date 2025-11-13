import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { login as loginRequest, getProfile } from '../api/auth.js';
import { setAuthToken } from '../api/client.js';

const AuthContext = createContext({
  user: null,
  token: null,
  loading: true,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  refreshProfile: async () => {}
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('checkme_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initialise = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const profile = await getProfile(token);
        setUser(profile);
      } catch (error) {
        console.error('Failed to restore session', error);
        localStorage.removeItem('checkme_token');
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    initialise();
  }, [token]);

  const login = async (email, password) => {
    const { access_token: jwt, role } = await loginRequest(email, password);
    localStorage.setItem('checkme_token', jwt);
    setToken(jwt);
    const profile = await getProfile(jwt);
    setUser({ ...profile, role });
  };

  const logout = () => {
    localStorage.removeItem('checkme_token');
    setAuthToken(null);
    setToken(null);
    setUser(null);
  };

  const refreshProfile = async () => {
    if (!token) return;
    const profile = await getProfile(token);
    setUser(profile);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      refreshProfile
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export const useAuth = () => useContext(AuthContext);
