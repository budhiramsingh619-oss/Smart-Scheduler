// CalendarPage.jsx
import { useState, useEffect } from 'react'
import { getTasks } from '../services/api'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, isSameDay, isToday } from 'date-fns'

export function CalendarPage() {
  const [tasks, setTasks] = useState([])
  const [current, setCurrent] = useState(new Date())
  const [selected, setSelected] = useState(null)

  useEffect(() => { getTasks().then(r => setTasks(r.data)) }, [])

  const days = eachDayOfInterval({ start: startOfMonth(current), end: endOfMonth(current) })
  const startPad = getDay(startOfMonth(current))

  const tasksOn = (day) => tasks.filter(t => t.deadline && isSameDay(new Date(t.deadline + 'T00:00:00'), day))

  const prev = () => setCurrent(d => new Date(d.getFullYear(), d.getMonth() - 1, 1))
  const next = () => setCurrent(d => new Date(d.getFullYear(), d.getMonth() + 1, 1))

  return (
    <div className="page">
      <div className="card">
        <div className="cal-nav">
          <button className="btn-sm" onClick={prev}>← Prev</button>
          <h2 className="cal-month">{format(current, 'MMMM yyyy')}</h2>
          <button className="btn-sm" onClick={next}>Next →</button>
        </div>

        <div className="cal-grid">
          {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
            <div key={d} className="cal-weekday">{d}</div>
          ))}
          {Array(startPad).fill(null).map((_, i) => <div key={'pad' + i} />)}
          {days.map(day => {
            const dt = tasksOn(day)
            return (
              <div
                key={day}
                className={`cal-day${isToday(day) ? ' today' : ''}`}
                onClick={() => setSelected({ day, tasks: dt })}
              >
                <div className="cal-day-num">{format(day, 'd')}</div>
                {dt.length > 0 && <div className="cal-day-badge">{dt.length}t</div>}
              </div>
            )
          })}
        </div>

        {selected && (
          <div className="cal-detail">
            <h3>{format(selected.day, 'EEEE, MMMM d, yyyy')}</h3>
            {selected.tasks.length === 0 ? (
              <div className="empty-state" style={{ marginTop: 10 }}><strong>No tasks</strong>Nothing on this date.</div>
            ) : (
              <div className="task-list" style={{ marginTop: 10 }}>
                {selected.tasks.map(t => (
                  <div key={t.id} className={`task-item${t.completed ? ' done' : ''}`}>
                    <span className={`priority-pip pip-${t.priority}`} />
                    <div className="task-body">
                      <div className="task-name">{t.name}</div>
                      <div className="task-meta">{t.category} · {t.priority} · {t.completed ? 'Completed' : 'Pending'}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default CalendarPage

// ── REMINDERS PAGE ──────────────────────────────────────────────────────────
export function RemindersPage() {
  const [tasks, setTasks] = useState([])

  useEffect(() => { getTasks().then(r => setTasks(r.data)) }, [])

  const daysLeft = (deadline) => {
    if (!deadline) return 999
    return Math.floor((new Date(deadline + 'T00:00:00') - new Date()) / 86400000)
  }

  const pending = [...tasks]
    .filter(t => !t.completed)
    .sort((a, b) => (a.deadline || '9999').localeCompare(b.deadline || '9999'))

  const urgencyClass = (dl) => dl < 0 ? 'days-overdue' : dl <= 2 ? 'days-urgent' : dl <= 7 ? 'days-soon' : 'days-ok'
  const urgencyLabel = (dl) => dl < 0 ? `${Math.abs(dl)}d overdue` : dl === 0 ? 'Due today' : `${dl}d left`
  const urgencyBg = (dl) => dl < 0 ? 'var(--red)' : dl <= 2 ? 'var(--amber)' : dl <= 7 ? 'var(--cyan)' : 'var(--green)'

  return (
    <div className="page">
      <div className="card">
        <div className="card-title"><span className="card-dot" />Upcoming Deadlines</div>
        {!pending.length ? (
          <div className="empty-state"><strong>All clear</strong>No pending tasks with deadlines.</div>
        ) : (
          <div className="reminder-list">
            {pending.map(t => {
              const dl = daysLeft(t.deadline)
              return (
                <div key={t.id} className="reminder-item">
                  <div className="reminder-urgency" style={{ background: urgencyBg(dl) }} />
                  <div className="reminder-body">
                    <div className="reminder-name">{t.name}</div>
                    <div className="reminder-meta">
                      {t.deadline ? new Date(t.deadline + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'No deadline'} · {t.category} · {t.priority}
                      {t.source === 'gmail' && <span className="badge-gmail"> 📧 From Gmail</span>}
                    </div>
                  </div>
                  <span className={`reminder-days ${urgencyClass(dl)}`}>{urgencyLabel(dl)}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
