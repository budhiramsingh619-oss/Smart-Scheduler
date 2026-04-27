import { createContext, useContext, useState, useEffect } from 'react'
import { getMe } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('ss_token')
    if (!token) { setLoading(false); return }
    getMe()
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem('ss_token'))
      .finally(() => setLoading(false))
  }, [])

  const signIn = (token, userData) => {
    localStorage.setItem('ss_token', token)
    setUser(userData)
  }

  const signOut = () => {
    localStorage.removeItem('ss_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, signIn, signOut, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
