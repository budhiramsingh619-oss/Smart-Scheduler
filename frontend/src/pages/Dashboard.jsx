import { useState, useEffect, useCallback } from 'react'
import { getDashboard, getTasks, addTask, completeTask, deleteTask } from '../services/api'
import StatCard from '../components/StatCard'
import TaskForm from '../components/TaskForm'
import TaskList from '../components/TaskList'
import InsightStrip from '../components/InsightStrip'

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const [db, tk] = await Promise.all([getDashboard(), getTasks()])
      setDashboard(db.data)
      setTasks(tk.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleAdd = async (data) => {
    await addTask(data)
    await load()
  }

  const handleComplete = async (id, focus) => {
    await completeTask(id, focus)
    await load()
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this task?')) return
    await deleteTask(id)
    await load()
  }

  if (loading) return <div className="page-loading">Loading dashboard…</div>

  const ins = dashboard?.insights || {}
  const bt = dashboard || {}

  return (
    <div className="page">
      <div className="stats-grid">
        <StatCard label="Total Tasks" value={dashboard?.total_tasks ?? 0} sub="All time" accent="violet" />
        <StatCard label="Completed" value={dashboard?.completed_tasks ?? 0} sub="Tasks done" accent="green" />
        <StatCard label="Pending" value={dashboard?.pending_tasks ?? 0} sub="To do" accent="amber" />
        <StatCard
          label="Best Hour"
          value={bt.best_hour !== undefined ? `${String(bt.best_hour).padStart(2, '0')}:00` : '--'}
          sub={`${Math.round((bt.best_hour_confidence || 0) * 100)}% confidence`}
          accent="cyan"
        />
      </div>

      <InsightStrip insights={ins} completionRate={dashboard?.completion_rate ?? 0} />

      <div className="dashboard-grid">
        <div className="dash-col">
          <div className="card">
            <div className="card-title"><span className="card-dot" />Add Task</div>
            <TaskForm onSubmit={handleAdd} />
          </div>
          <div className="card" style={{ marginTop: 14 }}>
            <div className="card-title"><span className="card-dot" />Task Manager</div>
            <TaskList tasks={tasks} onComplete={handleComplete} onDelete={handleDelete} />
          </div>
        </div>
      </div>
    </div>
  )
}
