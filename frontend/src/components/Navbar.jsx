import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/dashboard">🎓 AI Learning Journey</Link>
      </div>
      {user && (
        <div className="navbar-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/map">Learning Map</Link>
          <Link to="/profile">Profile</Link>
          <span className="navbar-user">Hi, {user.full_name?.split(" ")[0]}</span>
          <button onClick={handleLogout} className="btn btn-sm btn-outline">
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}
