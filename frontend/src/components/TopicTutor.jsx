import { useState, useRef, useEffect } from "react";
import { askTopicTutor } from "../api/endpoints";

export default function TopicTutor({ topicId, topicTitle }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastFailedQuestion, setLastFailedQuestion] = useState(null);
  const chatEndRef = useRef(null);

  const starterPrompts = [
    "Explain this topic simply",
    "Give me a real-world example",
    "What are the important points?",
    "I didn't understand this. Can you explain it differently?",
  ];

  // Auto-scroll to bottom of conversation when messages update or during loading
  useEffect(() => {
    if (messages.length > 0 || loading) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const handleAsk = async (promptText) => {
    const query = (promptText || question).trim();
    if (!query || loading) return;

    const userMessage = {
      id: Date.now(),
      role: "user",
      text: query,
    };

    // Format controlled recent message history (last 8 messages) for the backend
    const conversationHistory = messages.slice(-8).map((m) => ({
      role: m.role,
      content: m.role === "user" ? m.text : (m.data?.explanation || m.text || ""),
    }));

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setError("");
    setLastFailedQuestion(null);
    setLoading(true);

    try {
      const res = await askTopicTutor(topicId, {
        question: query,
        conversation_history: conversationHistory,
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        data: res.data,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setLastFailedQuestion(query);
      if (err.response?.status === 403) {
        setError("🔒 AI Tutor is only available for unlocked topics. Please unlock this topic first.");
      } else if (err.response?.status === 503) {
        setError(err.response?.data?.detail || "Gemini API key is not configured or service is temporarily unavailable.");
      } else if (err.response?.status === 504) {
        setError("AI Tutor request timed out connecting to Gemini. Please click Retry.");
      } else if (err.response?.status === 429) {
        setError("Gemini rate limit reached. Please wait a moment and click Retry.");
      } else {
        setError(err.response?.data?.detail || "Failed to reach AI Tutor. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastFailedQuestion) {
      handleAsk(lastFailedQuestion);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleAsk(question);
  };

  const handleClearChat = () => {
    setMessages([]);
    setQuestion("");
    setError("");
    setLastFailedQuestion(null);
  };

  // Helper to render natural text with paragraphs and inline code/blocks
  const renderFormattedText = (text) => {
    if (!text) return null;
    return text.split("\n\n").map((paragraph, pIdx) => {
      // Check for code blocks
      if (paragraph.startsWith("```") && paragraph.endsWith("```")) {
        const lines = paragraph.split("\n");
        const codeContent = lines.slice(1, -1).join("\n");
        return (
          <pre key={pIdx} className="code-block" style={{ margin: "8px 0" }}>
            <code>{codeContent}</code>
          </pre>
        );
      }
      return (
        <p key={pIdx} style={{ margin: "0 0 8px 0", lineHeight: 1.6 }}>
          {paragraph}
        </p>
      );
    });
  };

  return (
    <div className="card tutor-card">
      <div className="tutor-header">
        <div className="tutor-title-group">
          <span className="tutor-avatar">🤖</span>
          <div>
            <h3>AI Topic Tutor</h3>
            <p className="tutor-subtitle">
              Grounding in <strong>{topicTitle}</strong>
            </p>
          </div>
        </div>
        <div className="tutor-header-actions">
          <span className="tutor-scope-badge">Scoped: {topicTitle}</span>
          {messages.length > 0 && (
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={handleClearChat}
              title="Reset conversation"
            >
              🗑️ Clear Chat
            </button>
          )}
        </div>
      </div>

      {/* Empty State / Welcome */}
      {messages.length === 0 && !loading && (
        <div
          className="tutor-empty-state"
          style={{
            textAlign: "center",
            padding: "20px 14px",
            background: "#f8fafc",
            borderRadius: "10px",
            border: "1px dashed #cbd5e1",
            marginBottom: "16px",
          }}
        >
          <div style={{ fontSize: "2rem", marginBottom: "6px" }}>💡</div>
          <h4 style={{ color: "#3730a3", marginBottom: "4px", fontSize: "1rem" }}>
            Have doubts about {topicTitle}?
          </h4>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", maxWidth: "480px", margin: "0 auto 14px auto" }}>
            I am your dedicated tutor for this lesson. Ask me any question, or pick a starter prompt below:
          </p>
          <div className="prompts-chips" style={{ justifyContent: "center" }}>
            {starterPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="prompt-chip"
                disabled={loading}
                onClick={() => handleAsk(p)}
              >
                ✨ {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Quick Prompts chips for ongoing conversation */}
      {messages.length > 0 && (
        <div className="tutor-quick-prompts" style={{ marginBottom: "12px" }}>
          <span className="quick-prompts-label">Quick Follow-ups:</span>
          <div className="prompts-chips">
            {starterPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="prompt-chip"
                disabled={loading}
                onClick={() => handleAsk(p)}
              >
                💬 {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Continuous Conversation Thread */}
      {messages.length > 0 && (
        <div className="tutor-chat-thread">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`tutor-chat-row tutor-chat-row-${msg.role}`}
            >
              {msg.role === "user" ? (
                <div className="tutor-user-bubble">
                  <div className="tutor-user-bubble-header">
                    <span className="user-icon">👤 You</span>
                  </div>
                  <div className="tutor-user-text">{msg.text}</div>
                </div>
              ) : (
                <div className="tutor-assistant-card">
                  <div className="tutor-assistant-card-header">
                    <span className="tutor-badge-icon">🤖 AI Tutor</span>
                    {!msg.data?.is_topic_related && (
                      <span className="badge-warning-sm">⚠️ Lesson Scope Notice</span>
                    )}
                  </div>

                  {!msg.data?.is_topic_related && (
                    <div
                      className="alert alert-warning"
                      style={{ marginBottom: "12px", fontSize: "0.85rem", padding: "8px 12px" }}
                    >
                      Notice: This question is outside our current lesson on <em>{topicTitle}</em>.
                    </div>
                  )}

                  <div className="tutor-explanation" style={{ fontSize: "0.93rem" }}>
                    <div className="tutor-explanation-body">
                      {renderFormattedText(msg.data?.explanation || msg.text)}
                    </div>
                  </div>

                  {msg.data?.code_example && (
                    <div className="tutor-code-section" style={{ marginTop: "12px" }}>
                      <h4 style={{ fontSize: "0.85rem", marginBottom: "4px", color: "var(--text-muted)" }}>
                        💻 Code Example
                      </h4>
                      <pre className="code-block" style={{ margin: "4px 0" }}>
                        <code>{msg.data.code_example}</code>
                      </pre>
                    </div>
                  )}

                  {msg.data?.common_mistake && (
                    <div
                      className="tutor-mistake-box"
                      style={{
                        marginTop: "12px",
                        background: "#fffbeb",
                        borderLeft: "3px solid #f59e0b",
                        padding: "8px 12px",
                        borderRadius: "4px",
                        fontSize: "0.86rem",
                      }}
                    >
                      <strong style={{ color: "#b45309" }}>⚠️ Common Pitfall: </strong>
                      <span>{msg.data.common_mistake}</span>
                    </div>
                  )}

                  {msg.data?.practice_question && (
                    <div
                      className="tutor-practice-box"
                      style={{
                        marginTop: "12px",
                        background: "#f0fdf4",
                        borderLeft: "3px solid #22c55e",
                        padding: "8px 12px",
                        borderRadius: "4px",
                        fontSize: "0.86rem",
                      }}
                    >
                      <strong style={{ color: "#15803d" }}>🎯 Quick Self-Check: </strong>
                      <span>{msg.data.practice_question}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="tutor-loading-box">
          <div className="tutor-spinner"></div>
          <p>AI Tutor is preparing your explanation...</p>
        </div>
      )}

      {/* Error Message with Retry Option */}
      {error && (
        <div
          className="alert alert-error"
          style={{
            marginTop: "14px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "8px",
          }}
        >
          <span>{error}</span>
          {lastFailedQuestion && (
            <button
              type="button"
              className="btn btn-sm btn-outline"
              onClick={handleRetry}
              disabled={loading}
              style={{ background: "#ffffff", borderColor: "#dc2626", color: "#dc2626" }}
            >
              🔄 Retry
            </button>
          )}
        </div>
      )}

      {/* Input Form for Questions & Follow-ups */}
      <form onSubmit={handleFormSubmit} className="tutor-form" style={{ marginTop: "16px" }}>
        <div className="tutor-input-wrapper">
          <textarea
            rows={messages.length > 0 ? "2" : "3"}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={
              messages.length > 0
                ? `Ask a follow-up about ${topicTitle}... (e.g. why? or give another example)`
                : `Ask your AI Tutor about ${topicTitle}...`
            }
            disabled={loading}
            required
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleFormSubmit(e);
              }
            }}
          />
        </div>
        <div className="tutor-form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !question.trim()}
          >
            {loading ? "Thinking..." : messages.length > 0 ? "💬 Send Follow-up" : "💬 Ask AI Tutor"}
          </button>
        </div>
      </form>
    </div>
  );
}
