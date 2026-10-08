import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, createProfile, updateProfile } from "../api/endpoints";

const SKILL_LEVELS = ["beginner", "intermediate", "advanced"];
const LEARNING_STYLES = ["visual", "reading", "hands-on", "mixed"];
const EDUCATION_LEVELS = [
  "high_school", "undergraduate", "postgraduate", "professional",
];

export default function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    education_level: "undergraduate",
    target_goal: "",
    current_skill_level: "beginner",
    weekly_hours_available: 5,
    preferred_learning_style: "mixed",
  });

  useEffect(() => {
    getProfile()
      .then((res) => {
        setProfile(res.data);
        setForm(res.data);
      })
      .catch((err) => {
        // 404 = no profile yet — show creation form
        if (err.response?.status !== 404) {
          setError("Failed to load profile.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (e) => {
    const value =
      e.target.name === "weekly_hours_available"
        ? Number(e.target.value)
        : e.target.value;
    setForm({ ...form, [e.target.name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      let res;
      if (profile) {
        res = await updateProfile(form);
      } else {
        res = await createProfile(form);
      }
      setProfile(res.data);
      setForm(res.data);
      setIsEditing(false);
      setSuccess("Profile saved!");
      // After profile creation, redirect to create a learning map
      if (!profile) navigate("/map");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page-loading">Loading profile...</div>;

  const showForm = !profile || isEditing;

  return (
    <div className="page">
      <div className="page-header">
        <h1>📋 Learning Profile</h1>
        {profile && !isEditing && (
          <button className="btn btn-outline" onClick={() => setIsEditing(true)}>
            Edit Profile
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {!profile && !showForm && (
        <div className="empty-state">
          <p>You haven't created a learning profile yet.</p>
          <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
            Create Profile
          </button>
        </div>
      )}

      {showForm ? (
        <form onSubmit={handleSubmit} className="profile-form card">
          <div className="form-group">
            <label>Education Level</label>
            <select name="education_level" value={form.education_level} onChange={handleChange}>
              {EDUCATION_LEVELS.map((l) => (
                <option key={l} value={l}>{l.replace("_", " ")}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Learning Goal / Career Target</label>
            <input
              type="text"
              name="target_goal"
              value={form.target_goal}
              onChange={handleChange}
              placeholder="e.g. Python Developer, Web Developer"
              required
            />
          </div>

          <div className="form-group">
            <label>Current Skill Level</label>
            <select name="current_skill_level" value={form.current_skill_level} onChange={handleChange}>
              {SKILL_LEVELS.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>
              Weekly Study Hours: <strong>{form.weekly_hours_available}h</strong>
            </label>
            <input
              type="range"
              name="weekly_hours_available"
              min="1"
              max="40"
              value={form.weekly_hours_available}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Preferred Learning Style</label>
            <select name="preferred_learning_style" value={form.preferred_learning_style} onChange={handleChange}>
              {LEARNING_STYLES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving..." : profile ? "Update Profile" : "Create Profile"}
            </button>
            {profile && (
              <button type="button" className="btn btn-outline" onClick={() => setIsEditing(false)}>
                Cancel
              </button>
            )}
          </div>
        </form>
      ) : (
        <div className="profile-view card">
          <div className="profile-field">
            <span className="label">Education</span>
            <span>{profile.education_level?.replace("_", " ")}</span>
          </div>
          <div className="profile-field">
            <span className="label">Learning Goal</span>
            <span>{profile.target_goal}</span>
          </div>
          <div className="profile-field">
            <span className="label">Skill Level</span>
            <span className={`badge badge-${profile.current_skill_level}`}>
              {profile.current_skill_level}
            </span>
          </div>
          <div className="profile-field">
            <span className="label">Weekly Hours</span>
            <span>{profile.weekly_hours_available}h / week</span>
          </div>
          <div className="profile-field">
            <span className="label">Learning Style</span>
            <span>{profile.preferred_learning_style}</span>
          </div>
        </div>
      )}
    </div>
  );
}
