import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getTopic, getTopicContent, completeTopic, getAdaptiveRecommendation } from "../api/endpoints";
import TopicTutor from "../components/TopicTutor";



export default function TopicPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [adaptiveRec, setAdaptiveRec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState("");
  const [contentError, setContentError] = useState("");
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    const loadTopic = async () => {
      setLoading(true);
      setContentError("");
      try {
        // Step 1: Get topic metadata (fast)
        const res = await getTopic(id);
        setData(res.data);
        if (res.data.progress?.status?.toUpperCase() === "COMPLETED") setCompleted(true);

        // Step 2: If content is not included in the topic detail response, fetch/generate it
        if (!res.data.content) {
          setContentLoading(true);
          try {
            const contentRes = await getTopicContent(id);
            // Merge content into topic data
            setData(prev => ({ ...prev, content: contentRes.data }));
          } catch (contentErr) {
            if (contentErr.response?.status === 403) {
              setContentError("🔒 Topic is locked. Complete prerequisite topics first.");
            } else {
              setContentError("Content could not be generated. Please refresh to try again.");
            }
          } finally {
            setContentLoading(false);
          }
        }

        // Step 3: Fetch adaptive guidance if assessment was previously attempted
        getAdaptiveRecommendation(id)
          .then((recRes) => setAdaptiveRec(recRes.data))
          .catch(() => {});

      } catch (err) {
        if (err.response?.status === 403) {
          setError("🔒 This topic is locked. Complete the previous topic first.");
        } else {
          setError("Failed to load topic.");
        }
      } finally {
        setLoading(false);
      }
    };
    loadTopic();
  }, [id]);

  const handleComplete = async () => {
    setCompleting(true);
    setError("");
    try {
      await completeTopic(id);
      setCompleted(true);
      const res = await getTopic(id);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to mark as complete.");
    } finally {
      setCompleting(false);
    }
  };

  if (loading) return <div className="page-loading">Loading topic...</div>;
  if (error && !data)
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-outline" onClick={() => navigate("/map")}>
          ← Back to Map
        </button>
      </div>
    );

  const content = data.content;
  const progress_status = data.progress?.status?.toLowerCase() ?? "";

  return (
    <div className="page topic-page">
      {/* Header */}
      <div className="page-header">
        <button className="btn btn-sm btn-outline" onClick={() => navigate("/map")}>
          ← Map
        </button>
        <h1>{data.title}</h1>
        <span className={`status-badge status-${progress_status}`}>
          {progress_status?.replace("_", " ")}
        </span>
      </div>

      <div className="topic-meta-bar">
        <span>📊 {data.difficulty}</span>
        <span>⏱ {data.estimated_minutes} min</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Adaptive Guidance Alert if student needs revision */}
      {adaptiveRec && adaptiveRec.action === "REVIEW_AND_RETAKE" && (
        <div className="adaptive-topic-banner card">
          <div className="adaptive-topic-banner-title">
            🧠 <strong>Adaptive Feedback: Targeted Revision Needed</strong>
          </div>
          <p>{adaptiveRec.reason}</p>
          {adaptiveRec.weak_areas_guidance && adaptiveRec.weak_areas_guidance.length > 0 && (
            <div className="adaptive-topic-weak-items">
              <strong>Focus on these concepts while reading below:</strong>
              <ul>
                {adaptiveRec.weak_areas_guidance.map((w, idx) => (
                  <li key={idx}>
                    <strong>{w.concept_name}:</strong> {w.recommendation}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <button
            className="btn btn-primary btn-sm"
            style={{ marginTop: "10px" }}
            onClick={() => navigate(`/topics/${id}/assessment`)}
          >
            🎯 Retake Assessment Quiz
          </button>
        </div>
      )}

      {/* Content Sections */}

      <div className="content-sections">
        {content ? (
          <>
            {content.summary && (
              <div className="content-section card">
                <h2>📝 Summary</h2>
                <p>{content.summary}</p>
              </div>
            )}

            {content.explanation && (
              <div className="content-section card">
                <h2>📖 Explanation</h2>
                <div className="explanation-text">{content.explanation}</div>
              </div>
            )}

            {content.code_examples && (
              <div className="content-section card">
                <h2>💻 Code Examples</h2>
                <pre className="code-block"><code>{content.code_examples}</code></pre>
              </div>
            )}

            {content.common_mistakes && (
              <div className="content-section card">
                <h2>⚠️ Common Mistakes</h2>
                <p>{content.common_mistakes}</p>
              </div>
            )}

            {content.key_takeaways && (
              <div className="content-section card">
                <h2>🔑 Key Takeaways</h2>
                <p>{content.key_takeaways}</p>
              </div>
            )}
          </>
        ) : contentLoading ? (
          <div className="content-section card" style={{ textAlign: "center", padding: "40px" }}>
            <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📖</div>
            <h3 style={{ marginBottom: "8px" }}>Generating Personalized Learning Material...</h3>
            <p style={{ color: "var(--text-muted)", maxWidth: "500px", margin: "0 auto" }}>
              Our AI is assembling comprehensive explanations, practical examples, and common pitfalls tailored to your learning level. This may take 5–10 seconds.
            </p>
          </div>
        ) : contentError ? (
          <div className="content-section card">
            <div className="alert alert-error">{contentError}</div>
          </div>
        ) : (
          <div className="content-section card" style={{ textAlign: "center", padding: "30px" }}>
            <p style={{ color: "var(--text-muted)" }}>Content could not be loaded. Please refresh the page.</p>
          </div>
        )}
      </div>

      {/* AI Topic Tutor */}
      <TopicTutor topicId={id} topicTitle={data.title} />

      {/* Topic Actions: Quiz & Mark Complete */}
      <div className="topic-actions">


        <button
          className="btn btn-primary btn-lg"
          onClick={() => navigate(`/topics/${id}/assessment`)}
        >
          🎯 Take Assessment Quiz
        </button>

        {completed ? (
          <div className="completion-banner">
            ✅ Topic Completed! Next topic is now unlocked.
            <button className="btn btn-outline" onClick={() => navigate("/map")}>
              Continue in Map →
            </button>
          </div>
        ) : (
          <button
            className="btn btn-outline btn-lg"
            onClick={handleComplete}
            disabled={completing}
          >
            {completing ? "Marking complete..." : "✅ Mark as Complete"}
          </button>
        )}
      </div>
    </div>
  );
}
