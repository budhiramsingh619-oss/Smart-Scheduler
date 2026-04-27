import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import AIPanel from '../components/AIPanel'
import Dashboard from './Dashboard'
import SchedulePage from './SchedulePage'
import CalendarPage from './CalendarPage'
import ProductivityPage from './ProductivityPage'
import RemindersPage from './RemindersPage'
import IntegrationsPage from './IntegrationsPage'

export default function AppShell() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [aiOpen, setAiOpen] = useState(true)

  // Handle Google OAuth callback params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('google_connected') === 'true') {
      navigate('/', { replace: true })
      window.dispatchEvent(new CustomEvent('google-connected'))
    }
    if (params.get('error')) {
      navigate('/', { replace: true })
    }
  }, [])

  const pages = [
    { path: '/', label: 'Dashboard', icon: '◈' },
    { path: '/schedule', label: 'Schedule Hub', icon: '⊞' },
    { path: '/calendar', label: 'Calendar', icon: '◻' },
    { path: '/productivity', label: 'Productivity', icon: '◑' },
    { path: '/reminders', label: 'Reminders', icon: '◉' },
    { path: '/integrations', label: 'Integrations', icon: '⟳' },
  ]

  const currentPage = pages.find(p => p.path === location.pathname) || pages[0]

  return (
    <div className="app-shell">
      <Sidebar
        pages={pages}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentPath={location.pathname}
      />

      <div className="main-area">
        <Topbar
          title={currentPage.label}
          user={user}
          onMenuToggle={() => setSidebarOpen(v => !v)}
          onAIToggle={() => setAiOpen(v => !v)}
          aiOpen={aiOpen}
        />

        <div className="body-split">
          <div className="content-area">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/calendar" element={<CalendarPage />} />
              <Route path="/productivity" element={<ProductivityPage />} />
              <Route path="/reminders" element={<RemindersPage />} />
              <Route path="/integrations" element={<IntegrationsPage />} />
            </Routes>
          </div>

          <AIPanel open={aiOpen} />
        </div>
      </div>

      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  )
}
