import { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale,
  Filler, Tooltip, Legend
} from 'chart.js'
import { getDashboard } from '../services/api'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend)

export default function ProductivityPage() {
  const [data, setData] = useState(null)

  useEffect(() => {
    getDashboard().then(r => setData(r.data)).catch(console.error)
  }, [])

  if (!data) return <div className="page-loading">Loading analytics…</div>

  const ins = data.insights || {}
  const chartData = data.chart_data || []

  const lineData = {
    labels: chartData.map(d => `${d.hour}:00`),
    datasets: [{
      label: 'Avg Focus',
      data: chartData.map(d => d.avg_focus),
      borderColor: '#7c6af7',
      backgroundColor: 'rgba(124,106,247,0.08)',
      pointBackgroundColor: '#22d3ee',
      pointRadius: 5,
      pointHoverRadius: 7,
      fill: true,
      tension: 0.4,
      borderWidth: 2,
    }],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => ` Focus: ${ctx.parsed.y}/10 (${chartData[ctx.dataIndex]?.entries || 0} sessions)`,
        },
      },
    },
    scales: {
      y: { min: 0, max: 10, grid: { color: 'rgba(255,255,255,.05)' }, ticks: { color: '#7878a0', stepSize: 2 } },
      x: { grid: { color: 'rgba(255,255,255,.04)' }, ticks: { color: '#7878a0', autoSkip: false, maxRotation: 45 } },
    },
  }

  const metrics = [
    ['Completion Rate', `${ins.completion_rate || 0}%`],
    ['Avg Focus', `${ins.avg_focus || 0}/10`],
    ['Focus Consistency', `${ins.focus_consistency || 0}/10`],
    ['High Focus Ratio', `${ins.high_focus_ratio || 0}%`],
    ['Productivity Score', `${ins.productivity_score || 0}/100`],
    ['Trend', ins.trend || 'No Data'],
    ['Performance', ins.performance || 'No Data'],
    ['Completed (week)', ins.completed_tasks ?? 0],
  ]

  return (
    <div className="page">
      <div className="prod-grid">
        <div className="card">
          <div className="card-title"><span className="card-dot" />Focus by Hour of Day</div>
          <div style={{ height: 260 }}>
            <Line data={lineData} options={chartOptions} />
          </div>
          {ins.suggestion && (
            <div className="insight-callout" style={{ marginTop: 16 }}>
              💡 {ins.suggestion}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title"><span className="card-dot" />Analytics Summary</div>
          <div className="analytics-grid">
            {metrics.map(([label, val]) => (
              <div key={label} className="analytic-card">
                <div className="analytic-val">{val}</div>
                <div className="analytic-label">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
