// ── Sidebar ───────────────────────────────────────────────────────────────────
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Sidebar({ pages, open, onClose, currentPath }) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const go = (path) => { navigate(path); onClose() }

  return (
    <aside className={`sidebar${open ? ' open' : ''}`}>
      <div className="sb-logo">
        <div className="sb-logo-mark">SS</div>
        <span className="sb-logo-text">Smart Scheduler</span>
      </div>

      <div className="sb-section-label">Menu</div>
      <nav>
        {pages.map(p => (
          <button
            key={p.path}
            className={`nav-item${currentPath === p.path ? ' active' : ''}`}
            onClick={() => go(p.path)}
          >
            <span className="nav-bar" />
            <span className="nav-icon">{p.icon}</span>
            {p.label}
          </button>
        ))}
      </nav>

      <div className="sb-spacer" />

      <div className="sb-user">
        <div className="sb-user-info">
          <div className="sb-avatar">{user?.username?.[0]?.toUpperCase() || '?'}</div>
          <div>
            <div className="sb-username">{user?.username}</div>
            <div className="sb-since">{user?.email || 'No email linked'}</div>
          </div>
        </div>
        <button className="btn-logout" onClick={signOut}>Sign out</button>
      </div>
    </aside>
  )
}

export default Sidebar

// ── Topbar ────────────────────────────────────────────────────────────────────
import { useState, useEffect } from 'react'

export function Topbar({ title, onMenuToggle, onAIToggle, aiOpen }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
  useEffect(() => {
    const t = setInterval(() => setTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <header className="topbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <button className="btn-sm btn-mobile-menu" onClick={onMenuToggle}>☰</button>
        <h1 className="topbar-title">{title}</h1>
      </div>
      <div className="topbar-right">
        <div className="clock-badge">{time}</div>
        <button className={`btn-sm${aiOpen ? '' : ' btn-ai-closed'}`} onClick={onAIToggle}>
          🤖 AI {aiOpen ? '→' : '←'}
        </button>
      </div>
    </header>
  )
}

// ── StatCard ──────────────────────────────────────────────────────────────────
export function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`stat-card stat-${accent}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

// ── InsightStrip ──────────────────────────────────────────────────────────────
export function InsightStrip({ insights, completionRate }) {
  return (
    <div className="insight-strip">
      <div className="insight-card">
        <div className="insight-label">Weekly Insight</div>
        <div className="insight-text">{insights?.suggestion || 'Complete tasks to unlock weekly insights.'}</div>
      </div>
      <div className="insight-card">
        <div className="insight-label">Completion Rate</div>
        <div className="insight-big">{completionRate?.toFixed(1) || 0}%</div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${completionRate || 0}%` }} />
        </div>
        <div className="insight-text" style={{ marginTop: 7, fontSize: 12 }}>
          Trend: {insights?.trend || 'No Data'} · Performance: {insights?.performance || 'No Data'}
        </div>
      </div>
    </div>
  )
}

// ── TaskForm ──────────────────────────────────────────────────────────────────
import { useState as useFormState } from 'react'

export function TaskForm({ onSubmit, prefill }) {
  const today = new Date().toISOString().slice(0, 10)
  const [form, setForm] = useFormState({
    name: prefill?.name || '', category: '', deadline: today,
    priority: 'Medium', duration: 1, difficulty: 5, focus: 8, notes: '',
  })
  const [status, setStatus] = useFormState('')

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async () => {
    if (!form.name.trim()) { setStatus('Task name is required.'); return }
    if (!form.deadline) { setStatus('A deadline is required.'); return }
    setStatus('Saving…')
    try {
      await onSubmit({ ...form, duration: +form.duration, difficulty: +form.difficulty })
      setForm(f => ({ ...f, name: '', category: '', notes: '' }))
      setStatus('✅ Task added and schedule updated.')
    } catch (e) {
      setStatus('❌ ' + (e.response?.data?.error || 'Failed to add task.'))
    }
  }

  const reset = () => setForm({ name: '', category: '', deadline: today, priority: 'Medium', duration: 1, difficulty: 5, focus: 8, notes: '' })

  return (
    <div>
      <div className="task-form">
        <div className="form-field full">
          <div className="form-label">Task Name</div>
          <input className="form-input" value={form.name} onChange={set('name')} placeholder="e.g. Finish project report, Study chapter 4…" />
        </div>
        <div className="form-field">
          <div className="form-label">Category</div>
          <input className="form-input" value={form.category} onChange={set('category')} placeholder="Study, Work, Health…" />
        </div>
        <div className="form-field">
          <div className="form-label">Deadline</div>
          <input className="form-input" type="date" value={form.deadline} onChange={set('deadline')} />
        </div>
        <div className="form-field">
          <div className="form-label">Priority</div>
          <select className="form-input" value={form.priority} onChange={set('priority')}>
            <option>High</option><option>Medium</option><option>Low</option>
          </select>
        </div>
        <div className="form-field">
          <div className="form-label">Duration (hrs)</div>
          <select className="form-input" value={form.duration} onChange={set('duration')}>
            {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}h</option>)}
          </select>
        </div>
        <div className="form-field">
          <div className="form-label">Difficulty</div>
          <select className="form-input" value={form.difficulty} onChange={set('difficulty')}>
            <option value={3}>Easy (3)</option>
            <option value={5}>Medium (5)</option>
            <option value={8}>Hard (8)</option>
            <option value={10}>Very Hard (10)</option>
          </select>
        </div>
        <div className="form-field">
          <div className="form-label">Focus Rating</div>
          <select className="form-input" value={form.focus} onChange={set('focus')}>
            {[5,6,7,8,9,10].map(n => <option key={n} value={n}>{n}/10</option>)}
          </select>
        </div>
        <div className="form-actions">
          <button className="btn-ghost" type="button" onClick={reset}>Clear</button>
          <button className="btn-add" type="button" onClick={submit}>Add Task</button>
        </div>
      </div>
      {status && <div className={`form-status${status.startsWith('❌') ? ' error' : status.startsWith('✅') ? ' ok' : ''}`}>{status}</div>}
    </div>
  )
}

// ── TaskList ──────────────────────────────────────────────────────────────────
export function TaskList({ tasks, onComplete, onDelete }) {
  const [focus] = useFormState(8)

  const fmtDate = (v) => v ? new Date(v + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'No deadline'

  const sorted = [...tasks].sort((a, b) => {
    if (a.completed !== b.completed) return a.completed ? 1 : -1
    return (a.deadline || '9999').localeCompare(b.deadline || '9999')
  })

  if (!sorted.length) return <div className="empty-state"><strong>No tasks yet</strong>Add your first task above.</div>

  return (
    <div className="task-list">
      {sorted.map(t => (
        <div key={t.id} className={`task-item${t.completed ? ' done' : ''}`}>
          <span className={`priority-pip pip-${t.priority}`} />
          <div className="task-body">
            <div className="task-name">{t.name}{t.source === 'gmail' && <span className="badge-gmail-inline">📧</span>}</div>
            <div className="task-meta">{fmtDate(t.deadline)} · {t.category} · {t.priority} · {t.duration}h</div>
          </div>
          <div className="task-acts">
            <button className={`btn-done${t.completed ? ' undo' : ''}`} onClick={() => onComplete(t.id, focus)}>
              {t.completed ? 'Undo' : 'Done'}
            </button>
            <button className="btn-del" onClick={() => onDelete(t.id)}>✕</button>
          </div>
        </div>
      ))}
    </div>
  )
}
