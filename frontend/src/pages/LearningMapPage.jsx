import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getActiveLearningMap, advanceNextLevel } from "../api/endpoints";

const STATUS_ICON = {
  locked: "🔒",
  not_started: "⬜",
  in_progress: "🔵",
  completed: "✅",
};

const DIFFICULTY_COLOR = {
  beginner: "green",
  intermediate: "orange",
  advanced: "red",
};

export default function LearningMapPage() {
  const navigate = useNavigate();
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [advancing, setAdvancing] = useState(false);

  useEffect(() => {
    loadMap();
  }, []);

  const loadMap = () => {
    setLoading(true);
    getActiveLearningMap()
      .then((res) => setMapData(res.data))
      .catch((err) => {
        if (err.response?.status === 404) {
          setError("No active learning map. Go to Dashboard to generate one.");
        } else {
          setError("Failed to load learning map.");
        }
      })
      .finally(() => setLoading(false));
  };

  const handleAdvanceLevel = async () => {
    setAdvancing(true);
    setError("");
    try {
      await advanceNextLevel();
      loadMap();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to advance to the next level.");
    } finally {
      setAdvancing(false);
    }
  };

  if (loading) return <div className="page-loading">Loading learning map...</div>;

  const topics = mapData?.topics || [];
  const completedCount = topics.filter(
    (t) => (t.progress?.status || "").toLowerCase() === "completed"
  ).length;
  const totalCount = topics.length;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const isLevelCompleted = totalCount > 0 && completedCount === totalCount;
  const level = mapData?.learning_level || "beginner";

  return (
    <div className="page">
      <div className="page-header">
        <h1>🗺️ Learning Map</h1>
        {mapData && (
          <>
            <span className="goal-badge">{mapData.goal_title}</span>
            <span
              className="badge"
              style={{
                background:
                  level === "advanced"
                    ? "#fee2e2"
                    : level === "intermediate"
                    ? "#fef3c7"
                    : "#dcfce7",
                color:
                  level === "advanced"
                    ? "#991b1b"
                    : level === "intermediate"
                    ? "#92400e"
                    : "#166534",
                fontWeight: 600,
                fontSize: "0.85rem",
                padding: "4px 10px",
                borderRadius: "16px",
              }}
            >
              🏷️ {level.toUpperCase()} LEVEL
            </span>
          </>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {mapData && (
        <>
          {/* Progress summary banner */}
          <div
            className="card"
            style={{
              marginBottom: "20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div>
              <strong style={{ fontSize: "1.05rem" }}>Curriculum Progress:</strong>
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "2px" }}>
                {completedCount} of {totalCount} topics mastered ({progressPct}%)
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: "200px" }}>
              <div
                style={{
                  flex: 1,
                  background: "#e5e7eb",
                  borderRadius: "8px",
                  height: "10px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${progressPct}%`,
                    background: "var(--primary)",
                    height: "100%",
                    transition: "width 0.4s ease",
                  }}
                />
              </div>
              <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>{progressPct}%</span>
            </div>
          </div>

          {/* Level completion celebration banner */}
          {isLevelCompleted && (
            <div
              className="card"
              style={{
                background: "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)",
                border: "2px solid #818cf8",
                marginBottom: "24px",
                padding: "20px",
                borderRadius: "12px",
                textAlign: "center",
              }}
            >
              <h2 style={{ fontSize: "1.3rem", color: "#3730a3", marginBottom: "8px" }}>
                🎉 {level.toUpperCase()} LEVEL COMPLETED!
              </h2>
              <p style={{ color: "#4338ca", marginBottom: "16px" }}>
                You have passed all {totalCount} topic assessments in this curriculum!
              </p>
              {level !== "advanced" ? (
                <button
                  className="btn btn-primary"
                  onClick={handleAdvanceLevel}
                  disabled={advancing}
                  style={{ padding: "10px 24px", fontSize: "1rem" }}
                >
                  {advancing
                    ? "Generating Next Level..."
                    : `🚀 Advance to ${
                        level === "beginner" ? "Intermediate" : "Advanced"
                      } Level →`}
                </button>
              ) : (
                <div style={{ fontWeight: 700, color: "#166534" }}>
                  🏆 Grand Mastery Achieved! You have completed the entire Advanced Journey.
                </div>
              )}
            </div>
          )}

          <p className="map-description" style={{ marginBottom: "18px" }}>
            {mapData.description}
          </p>

          <div className="topics-list">
            {topics.map((topic, index) => {
              const progressStatus = topic.progress?.status?.toLowerCase() ?? "locked";
              const isLocked = progressStatus === "locked";
              return (
                <div
                  key={topic.id}
                  className={`topic-card ${isLocked ? "topic-locked" : "topic-available"}`}
                  onClick={() => !isLocked && navigate(`/topics/${topic.id}`)}
                >
                  <div className="topic-number">#{index + 1}</div>
                  <div className="topic-info">
                    <div className="topic-title">
                      <span className="status-icon">
                        {STATUS_ICON[progressStatus] || "⬜"}
                      </span>
                      {topic.title}
                    </div>
                    <div className="topic-meta">
                      <span
                        className="difficulty-tag"
                        style={{ color: DIFFICULTY_COLOR[topic.difficulty] }}
                      >
                        {topic.difficulty}
                      </span>
                      <span className="time-tag">⏱ {topic.estimated_minutes} min</span>
                    </div>
                    {topic.description && (
                      <p className="topic-desc">{topic.description}</p>
                    )}
                  </div>
                  <div className="topic-arrow">
                    {isLocked ? "🔒" : "→"}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

