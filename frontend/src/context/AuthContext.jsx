import { createContext, useContext, useState, useEffect } from "react";
import { getMe } from "../api/endpoints";

const AuthContext = createContext(null);

/**
 * AuthProvider wraps the whole app and provides:
 *   - user: the logged-in user object (or null)
 *   - login(token): save token, load user
 *   - logout(): clear everything
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true while checking existing token

  // On first load, check if a token is already saved
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      getMe()
        .then((res) => setUser(res.data))
        .catch(() => localStorage.removeItem("access_token"))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const loginUser = async (token) => {
    localStorage.setItem("access_token", token);
    const res = await getMe();
    setUser(res.data);
  };

  const logoutUser = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
