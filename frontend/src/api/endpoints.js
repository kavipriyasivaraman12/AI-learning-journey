import api from "./apiClient";

// ── Auth ─────────────────────────────────────────────────────────────────────

export const register = (data) => api.post("/auth/register", data);
export const login = (data) => api.post("/auth/login", data);
export const getMe = () => api.get("/auth/me");

// ── Learning Profile ─────────────────────────────────────────────────────────

export const getProfile = () => api.get("/profile");
export const createProfile = (data) => api.post("/profile", data);
export const updateProfile = (data) => api.put("/profile", data);

// ── Learning Maps ────────────────────────────────────────────────────────────

export const createLearningMap = (data) => api.post("/learning-maps", data);
export const advanceNextLevel = () => api.post("/learning-maps/next-level", {});
export const getActiveLearningMap = () => api.get("/learning-maps/active");
export const getLearningMap = (id) => api.get(`/learning-maps/${id}`);
export const getAllLearningMaps = () => api.get("/learning-maps");

// ── Topics ───────────────────────────────────────────────────────────────────

export const getTopic = (id) => api.get(`/topics/${id}`);
export const getTopicContent = (id) => api.get(`/topics/${id}/content`);
export const completeTopic = (id) => api.post(`/topics/${id}/complete`, {});

// ── Progress / Dashboard ─────────────────────────────────────────────────────

export const getDashboard = () => api.get("/progress/dashboard");

// ── Assessments & Adaptive Learning ──────────────────────────────────────────

export const getTopicAssessment = (topicId) => api.get(`/topics/${topicId}/assessment`);
export const submitAssessment = (assessmentId, data) => api.post(`/assessments/${assessmentId}/submit`, data);
export const getAssessmentAttempts = (assessmentId) => api.get(`/assessments/${assessmentId}/attempts`);
export const getAdaptiveRecommendation = (topicId) => api.get(`/topics/${topicId}/adaptive-recommendation`);
// ── AI Topic Tutor ──────────────────────────────────────────────────────────

export const askTopicTutor = (topicId, data) => api.post(`/topics/${topicId}/tutor`, data);
