import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getTopicAssessment, submitAssessment } from "../api/endpoints";

export default function AssessmentPage() {
  const { id: topicId } = useParams();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState(null);

  useEffect(() => {
    loadAssessment();
  }, [topicId]);

  const loadAssessment = async () => {
    setLoading(true);
    setError("");
    setReport(null);
    setAnswers({});
    try {
      const res = await getTopicAssessment(topicId);
      setAssessment(res.data);
    } catch (err) {
      if (err.response?.status === 403) {
        setError("🔒 This topic's assessment is locked. Please unlock the prerequisite topics first.");
      } else {
        setError(err.response?.data?.detail || "Failed to load assessment.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (questionId, optionIndex) => {
    if (report) return; // Prevent changing after submission
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!assessment) return;

    // Verify all questions are answered
    const unanswered = assessment.questions.filter((q) => answers[q.id] === undefined);
    if (unanswered.length > 0) {
      setError(`Please answer all questions before submitting (${unanswered.length} remaining).`);
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const payload = {
        answers: Object.entries(answers).map(([question_id, selected_option_index]) => ({
          question_id,
          selected_option_index,
        })),
        selected_question_ids: assessment.questions.map((q) => q.id),
      };
      const res = await submitAssessment(assessment.id, payload);
      setReport(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetake = () => {
    setReport(null);
    setAnswers({});
    setError("");
    // Re-fetch assessment to get a NEW randomized set of 15 questions
    loadAssessment();
  };

  if (loading) return <div className="page-loading">Generating / Loading Assessment...</div>;

  if (error && !assessment) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-outline" onClick={() => navigate(`/topics/${topicId}`)}>
          ← Back to Topic
        </button>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;
  const totalQuestions = assessment?.questions?.length || 0;

  return (
    <div className="page assessment-page">
      {/* Header */}
      <div className="page-header">
        <button className="btn btn-sm btn-outline" onClick={() => navigate(`/topics/${topicId}`)}>
          ← Topic Content
        </button>
        <h1>🎯 {assessment?.title}</h1>
        <span className="goal-badge">Pass Mark: {assessment?.passing_score_percentage}%</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Scorecard / Results View */}
      {report && (
        <div className="card scorecard-card">
          <div className="scorecard-header">
            <div className="scorecard-grade">
              <span className="score-number">{report.score_percentage}%</span>
              <span className="score-ratio">
                ({report.correct_answers_count}/{report.total_questions} Correct)
              </span>
            </div>
            <div className="scorecard-status">
              {report.passed ? (
                <div className="badge-pass">🎉 PASSED</div>
              ) : (
                <div className="badge-fail">⚠️ NEEDS IMPROVEMENT</div>
              )}
            </div>
          </div>

          {/* Weak Areas */}
          {report.weak_areas && report.weak_areas.length > 0 ? (
            <div className="weak-areas-section">
              <h3>🔍 Identified Weak Areas to Review:</h3>
              <div className="weak-areas">
                {report.weak_areas.map((wa, idx) => (
                  <span key={idx} className="weak-area-tag">
                    {wa}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="alert alert-success" style={{ marginTop: "12px" }}>
              🌟 Excellent work! You answered all questions correctly with zero weak areas detected.
            </div>
          )}

          {/* Adaptive Learning Recommendation Section */}
          {report.adaptive_recommendation && (
            <div className="adaptive-recommendation-box">
              <div className="adaptive-box-header">
                <span className="adaptive-icon">🧠</span>
                <div>
                  <h4>Personalized Next-Step Recommendation</h4>
                  <p className="adaptive-action-label">
                    Action: <strong>{report.adaptive_recommendation.action.replace(/_/g, " ")}</strong>
                  </p>
                </div>
              </div>

              <div className="adaptive-reason-block">
                <strong>Why this recommendation:</strong>
                <p>{report.adaptive_recommendation.reason}</p>
              </div>

              <div className="adaptive-next-step-block">
                <strong>Next Step:</strong>
                <p>{report.adaptive_recommendation.next_step}</p>
              </div>

              {/* Weak Areas Targeted Guidance */}
              {report.adaptive_recommendation.weak_areas_guidance &&
                report.adaptive_recommendation.weak_areas_guidance.length > 0 && (
                  <div className="weak-guidance-list">
                    <h5>🎯 Targeted Study Advice for Weak Areas:</h5>
                    <ul>
                      {report.adaptive_recommendation.weak_areas_guidance.map((wag, idx) => (
                        <li key={idx}>
                          <strong>{wag.concept_name}:</strong> {wag.recommendation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          )}

          {/* Action buttons */}
          <div className="scorecard-actions">
            {report.passed && report.adaptive_recommendation?.next_topic_id ? (
              <button
                className="btn btn-primary"
                onClick={() => navigate(`/topics/${report.adaptive_recommendation.next_topic_id}`)}
              >
                🚀 Advance to {report.adaptive_recommendation.next_topic_title || "Next Topic"} →
              </button>
            ) : null}

            {!report.passed && (
              <button className="btn btn-primary" onClick={handleRetake}>
                🔄 Retake Quiz
              </button>
            )}

            <button className="btn btn-outline" onClick={() => navigate(`/topics/${topicId}`)}>
              📖 Review Topic Material
            </button>
            <button className="btn btn-outline" onClick={() => navigate("/map")}>
              🗺️ Back to Map
            </button>
          </div>
        </div>
      )}


      {/* Questions Form / Review */}
      <form onSubmit={handleSubmit} className="assessment-questions-list">
        {assessment?.questions?.map((question, qIdx) => {
          const selectedOption = answers[question.id];
          const resultDetail = report?.question_results?.find((r) => r.question_id === question.id);

          return (
            <div
              key={question.id}
              className={`card question-card ${
                resultDetail
                  ? resultDetail.is_correct
                    ? "question-correct"
                    : "question-incorrect"
                  : ""
              }`}
            >
              <div className="question-header">
                <span className="question-num">Question {qIdx + 1} of {totalQuestions}</span>
                {resultDetail && (
                  <span className={`result-badge ${resultDetail.is_correct ? "badge-success" : "badge-danger"}`}>
                    {resultDetail.is_correct ? "✓ Correct" : "✗ Incorrect"}
                  </span>
                )}
              </div>

              <p className="question-prompt">{question.question_text}</p>

              <div className="options-grid">
                {question.options.map((optText, optIdx) => {
                  const isSelected = selectedOption === optIdx;
                  let optionClass = "option-label";

                  if (resultDetail) {
                    if (optIdx === resultDetail.correct_option_index) {
                      optionClass += " option-correct";
                    } else if (isSelected && !resultDetail.is_correct) {
                      optionClass += " option-wrong";
                    }
                  } else if (isSelected) {
                    optionClass += " option-selected";
                  }

                  return (
                    <label key={optIdx} className={optionClass}>
                      <input
                        type="radio"
                        name={`question_${question.id}`}
                        checked={isSelected}
                        onChange={() => handleSelectOption(question.id, optIdx)}
                        disabled={report !== null}
                      />
                      <span className="option-letter">
                        {String.fromCharCode(65 + optIdx)}.
                      </span>
                      <span className="option-text">{optText}</span>
                    </label>
                  );
                })}
              </div>

              {/* Explanation after submission */}
              {resultDetail && (
                <div className="question-explanation">
                  <strong>💡 Explanation: </strong>
                  {resultDetail.explanation}
                </div>
              )}
            </div>
          );
        })}

        {/* Submit Bar when not yet submitted */}
        {!report && (
          <div className="submit-bar card">
            <span>
              Progress: <strong>{answeredCount}</strong> of <strong>{totalQuestions}</strong> answered
            </span>
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={submitting || answeredCount < totalQuestions}
            >
              {submitting ? "Evaluating..." : "Submit Assessment"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
