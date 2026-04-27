import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { login, register } from '../services/api'

export default function AuthPage() {
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState('')
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async () => {
    setMsg(''); setMsgType('')
    try {
      const fn = tab === 'login' ? login : register
      const r = await fn(form)
      signIn(r.data.token, r.data.user)
      navigate('/')
    } catch (e) {
      setMsg(e.response?.data?.error || 'Something went wrong.')
      setMsgType('error')
    }
  }

  const handleKey = (e) => { if (e.key === 'Enter') submit() }

  return (
    <div className="auth-page">
      <div className="auth-wrap">
        <div className="auth-logo">
          <div className="auth-logo-mark">SS</div>
          <span>Smart Scheduler AI</span>
        </div>

        <div className="auth-tabs">
          <button className={`auth-tab${tab === 'login' ? ' active' : ''}`} onClick={() => { setTab('login'); setMsg('') }}>Sign in</button>
          <button className={`auth-tab${tab === 'signup' ? ' active' : ''}`} onClick={() => { setTab('signup'); setMsg('') }}>Create account</button>
        </div>

        <div className="field-group">
          <div className="field-label">Username</div>
          <input className="field-input" value={form.username} onChange={set('username')} onKeyDown={handleKey} placeholder="Enter your username" autoComplete="username" />
        </div>

        {tab === 'signup' && (
          <div className="field-group">
            <div className="field-label">Email (optional)</div>
            <input className="field-input" type="email" value={form.email} onChange={set('email')} onKeyDown={handleKey} placeholder="your@email.com" />
          </div>
        )}

        <div className="field-group">
          <div className="field-label">Password</div>
          <input className="field-input" type="password" value={form.password} onChange={set('password')} onKeyDown={handleKey} placeholder={tab === 'login' ? 'Enter your password' : 'Choose a password (min 6 chars)'} autoComplete={tab === 'login' ? 'current-password' : 'new-password'} />
        </div>

        <button className="btn-primary" onClick={submit}>{tab === 'login' ? 'Sign in' : 'Create account'}</button>

        {msg && <p className={`auth-msg${msgType ? ' ' + msgType : ''}`}>{msg}</p>}
      </div>
    </div>
  )
}
