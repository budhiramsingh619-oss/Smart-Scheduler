import { useState, useEffect } from 'react'
import { getSchedule, regenerateSchedule, completeTask, getTasks } from '../services/api'

export default function SchedulePage() {
  const [schedule, setSchedule] = useState([])
  const [bestHour, setBestHour] = useState(null)
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [s, t] = await Promise.all([getSchedule(), getTasks()])
      setSchedule(s.data.schedule || [])
      setBestHour(s.data.best_hour)
      setTasks(t.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleRegenerate = async () => {
    setLoading(true)
    const r = await regenerateSchedule()
    setSchedule(r.data.schedule || [])
    setBestHour(r.data.best_hour)
    setLoading(false)
  }

  const handleDone = async (id) => {
    await completeTask(id, 8)
    await load()
  }

  const priorityColor = (p) => p === 'High' ? 'var(--red)' : p === 'Low' ? 'var(--green)' : 'var(--amber)'

  if (loading) return <div className="page-loading">Building your schedule…</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          {bestHour !== null && (
            <p className="page-meta">Your best focus hour today: <strong style={{ color: 'var(--cyan)' }}>{String(bestHour).padStart(2, '0')}:00</strong></p>
          )}
        </div>
        <button className="btn-accent" onClick={handleRegenerate}>↺ Regenerate</button>
      </div>

      <div className="card">
        <div className="card-title"><span className="card-dot" />Today's Smart Schedule</div>
        {schedule.length === 0 ? (
          <div className="empty-state"><strong>No schedule yet</strong>Add tasks on the Dashboard and hit Regenerate.</div>
        ) : (
          <div className="timeline">
            {schedule.map((item, i) => (
              <div key={item.id} className="timeline-item">
                <div className="timeline-line">
                  <div className="timeline-dot" style={{ borderColor: priorityColor(item.priority) }} />
                  {i < schedule.length - 1 && <div className="timeline-connector" />}
                </div>
                <div className="timeline-time">{item.start}–{item.end}</div>
                <div className="timeline-body">
                  <div className="timeline-name">{item.task}</div>
                  <div className="timeline-meta">{item.category} · {item.priority} · Difficulty {item.difficulty}/10 · Score {item.score}</div>
                  <span className="badge badge-task">📋 TASK</span>
                  <button className="btn-done-inline" onClick={() => handleDone(item.id)}>Mark Done</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pending tasks not in schedule */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-title"><span className="card-dot" />All Pending Tasks</div>
        <div className="task-table">
          {tasks.filter(t => !t.completed).map(t => (
            <div key={t.id} className="task-row">
              <span className="pip" style={{ background: priorityColor(t.priority) }} />
              <span className="task-row-name">{t.name}</span>
              <span className="task-row-cat">{t.category}</span>
              <span className="task-row-date">{t.deadline || 'No deadline'}</span>
              <span className="badge" style={{ background: 'rgba(124,106,247,.15)', color: 'var(--accent2)' }}>{t.priority}</span>
              {t.scheduled_start ? (
                <span className="task-row-scheduled">{t.scheduled_start}–{t.scheduled_end}</span>
              ) : (
                <span className="task-row-unscheduled">Unscheduled</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
