import axios from 'axios'

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}`
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ss_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ss_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const register = (data) => api.post('/auth/register', data)
export const login = (data) => api.post('/auth/login', data)
export const getMe = () => api.get('/auth/me')
export const updatePreferences = (data) => api.patch('/auth/preferences', data)

// Tasks
export const getTasks = () => api.get('/tasks/')
export const addTask = (data) => api.post('/tasks/', data)
export const updateTask = (id, data) => api.patch(`/tasks/${id}`, data)
export const completeTask = (id, focus) => api.post(`/tasks/${id}/complete`, { focus })
export const deleteTask = (id) => api.delete(`/tasks/${id}`)

// Schedule
export const getSchedule = () => api.get('/schedule/')
export const regenerateSchedule = () => api.post('/schedule/regenerate')

// Dashboard
export const getDashboard = () => api.get('/dashboard/')

// Google
export const getGoogleAuthUrl = () => api.get('/auth/google/login')
export const syncGmail = () => api.post('/auth/google/sync-gmail')
export const pushToCalendar = () => api.post('/auth/google/push-calendar')
export const disconnectGoogle = () => api.delete('/auth/google/disconnect')

// AI
export const askAI = (question) => api.post('/ai/chat', { question })
