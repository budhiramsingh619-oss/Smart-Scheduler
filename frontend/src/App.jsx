import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import AuthPage from './pages/AuthPage'
import AppShell from './pages/AppShell'

function Guard({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="app-loading"><div className="spinner" /></div>
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/*" element={<Guard><AppShell /></Guard>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
