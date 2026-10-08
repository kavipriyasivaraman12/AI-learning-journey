import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProfilePage from "./pages/ProfilePage";
import DashboardPage from "./pages/DashboardPage";
import LearningMapPage from "./pages/LearningMapPage";
import TopicPage from "./pages/TopicPage";
import AssessmentPage from "./pages/AssessmentPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        {/* Navbar is always shown (it hides links if not logged in) */}
        <Navbar />

        <main className="main-content">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes — require JWT */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/map"
              element={
                <ProtectedRoute>
                  <LearningMapPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/topics/:id"
              element={
                <ProtectedRoute>
                  <TopicPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/topics/:id/assessment"
              element={
                <ProtectedRoute>
                  <AssessmentPage />
                </ProtectedRoute>
              }
            />


            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  );
}
