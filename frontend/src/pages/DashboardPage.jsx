import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboard, createLearningMap, advanceNextLevel, getProfile } from "../api/endpoints";

export default function DashboardPage() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [generating, setGenerating] = useState(false);
  const [advancing, setAdvancing] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await getDashboard();
      setDashboard(res.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setDashboard(null); // No active map
      } else {
        setError("Failed to load dashboard.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMap = async () => {
    setGenerating(true);
    setError("");
    try {
      const profileRes = await getProfile();
      await createLearningMap({
        goal_title: profileRes.data.target_goal,
        learning_level: profileRes.data.current_skill_level,
        force_regenerate: false,
      });
      await loadDashboard();
    } catch (err) {
      if (err.response?.status === 404) {
        setError("Please create a learning profile first.");
        navigate("/profile");
      } else {
        setError(err.response?.data?.detail || "Failed to generate learning map.");
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleAdvanceLevel = async () => {
    setAdvancing(true);
    setError("");
    try {
      await advanceNextLevel();
      await loadDashboard();
      navigate("/map");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to advance to next level.");
    } finally {
      setAdvancing(false);
    }
  };

  if (loading) return <div className="page-loading">Loading dashboard...</div>;

  // No learning map yet
  if (!dashboard || !dashboard.active_roadmap_id) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>🏠 Dashboard</h1>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="empty-state card">
          <div className="empty-icon">🗺️</div>
          <h2>No Learning Map Yet</h2>
          <p>Generate a personalized learning map containing 25–30 topics based on your profile.</p>
          <button
            className="btn btn-primary btn-lg"
            onClick={handleGenerateMap}
            disabled={generating}
          >
            {generating ? "Generating Your Journey..." : "🚀 Generate My Learning Map"}
          </button>
        </div>
      </div>
    );
  }

  const {
    goal_title,
    learning_level = "beginner",
    total_topics_count,
    completed_topics_count,
    overall_progress_percentage,
    average_score,
    weak_areas_summary,
    current_topic,
    recommendation_reason,
    is_level_completed,
    next_level_available,
  } = dashboard;

  return (
    <div className="page">
      <div className="page-header">
        <h1>🏠 Dashboard</h1>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span className="goal-badge">{goal_title}</span>
          <span className={`badge badge-${learning_level?.toLowerCase() || "beginner"}`}>
            Level: {learning_level?.toUpperCase()}
          </span>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Level Completion Celebration Banner */}
      {is_level_completed && (
        <div className="card level-completion-card" style={{ border: "2px solid #16a34a", background: "#f0fdf4" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "12px" }}>
            <span style={{ fontSize: "2.4rem" }}>🎉</span>
            <div>
              <h2 style={{ color: "#166534", fontSize: "1.3rem" }}>
                {learning_level?.toUpperCase()} {goal_title} Journey Completed!
              </h2>
              <p style={{ color: "#15803d", fontSize: "0.95rem" }}>
                You have mastered all {total_topics_count} topics in this roadmap with an average score of {average_score != null ? `${average_score?.toFixed(0)}%` : "100%"}.
              </p>
            </div>
          </div>

          {next_level_available ? (
            <div style={{ background: "#ffffff", padding: "16px", borderRadius: "8px", border: "1px solid #86efac", marginTop: "10px" }}>
              <p style={{ fontWeight: 600, color: "#166534", marginBottom: "10px" }}>
                Ready to take the next step in your individualized journey?
              </p>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleAdvanceLevel}
                  disabled={advancing}
                >
                  {advancing ? "Generating Next Level..." : `🚀 Continue to ${next_level_available.toUpperCase()} ${goal_title} →`}
                </button>
                <button
                  className="btn btn-outline"
                  onClick={() => navigate("/map")}
                >
                  🗺️ Review Completed Map
                </button>
              </div>
            </div>
          ) : (
            <div style={{ background: "#ffffff", padding: "14px", borderRadius: "8px", border: "1px solid #86efac", marginTop: "10px" }}>
              🏆 <strong>Master Tier Achieved!</strong> You have conquered the Advanced roadmap for {goal_title}.
            </div>
          )}
        </div>
      )}

      {/* Progress Overview */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{completed_topics_count}/{total_topics_count}</div>
          <div className="stat-label">Topics Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{overall_progress_percentage}%</div>
          <div className="stat-label">Overall Progress</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {average_score != null ? `${average_score?.toFixed(0)}%` : "—"}
          </div>
          <div className="stat-label">Avg Mastery Score</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="card">
        <div className="card-title">Learning Progress</div>
        <div className="progress-bar-container">
          <div
            className="progress-bar-fill"
            style={{ width: `${overall_progress_percentage || 0}%` }}
          />
        </div>
        <div className="progress-label">{overall_progress_percentage || 0}% complete ({completed_topics_count} of {total_topics_count} topics)</div>
      </div>

      {/* Continue Learning */}
      {current_topic && !is_level_completed && (
        <div className="card continue-card">
          <div className="card-title">▶️ Continue Learning</div>
          <div className="continue-topic">
            <div>
              <h3>{current_topic.title}</h3>
              <span className={`status-badge status-${current_topic.status?.toLowerCase()}`}>
                {current_topic.status?.replace("_", " ")}
              </span>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => navigate(`/topics/${current_topic.topic_id}`)}
            >
              Continue Topic →
            </button>
          </div>
        </div>
      )}

      {/* AI Recommendation */}
      {recommendation_reason && (
        <div className="card recommendation-card">
          <div className="card-title">💡 Recommendation</div>
          <p>{recommendation_reason}</p>
        </div>
      )}

      {/* Weak Areas */}
      {weak_areas_summary?.length > 0 && (
        <div className="card">
          <div className="card-title">⚠️ Areas to Improve</div>
          <div className="weak-areas">
            {weak_areas_summary.map((area, i) => (
              <span key={i} className="weak-area-tag">{area}</span>
            ))}
          </div>
        </div>
      )}

      {/* Go to full map */}
      <div className="dashboard-actions">
        <button className="btn btn-outline" onClick={() => navigate("/map")}>
          View Full Learning Map ({total_topics_count} Topics)
        </button>
      </div>
    </div>
  );
}
