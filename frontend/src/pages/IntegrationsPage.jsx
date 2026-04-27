import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { getMe, getGoogleAuthUrl, syncGmail, pushToCalendar, disconnectGoogle } from '../services/api'

export default function IntegrationsPage() {
  const { user, setUser } = useAuth()
  const [status, setStatus] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [pushing, setPushing] = useState(false)

  useEffect(() => {
    const onConnected = async () => {
      const r = await getMe()
      setUser(r.data)
      setStatus('Google account connected successfully!')
    }
    window.addEventListener('google-connected', onConnected)
    return () => window.removeEventListener('google-connected', onConnected)
  }, [])

  const connectGoogle = async () => {
    const r = await getGoogleAuthUrl()
    window.location.href = r.data.auth_url
  }

  const handleGmailSync = async () => {
    setSyncing(true)
    setStatus('')
    try {
      const r = await syncGmail()
      const { synced, skipped, tasks_created } = r.data
      setStatus(`✅ Gmail sync complete: ${synced} task${synced !== 1 ? 's' : ''} created, ${skipped} emails skipped.${tasks_created.length ? '\n\nNew tasks:\n• ' + tasks_created.join('\n• ') : ''}`)
    } catch (e) {
      setStatus('❌ ' + (e.response?.data?.error || 'Gmail sync failed.'))
    } finally {
      setSyncing(false)
    }
  }

  const handleCalendarPush = async () => {
    setPushing(true)
    setStatus('')
    try {
      const r = await pushToCalendar()
      setStatus(`✅ Calendar sync: ${r.data.pushed} events created, ${r.data.updated} updated.`)
    } catch (e) {
      setStatus('❌ ' + (e.response?.data?.error || 'Calendar sync failed.'))
    } finally {
      setPushing(false)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm('Disconnect your Google account?')) return
    await disconnectGoogle()
    const r = await getMe()
    setUser(r.data)
    setStatus('Google account disconnected.')
  }

  const connected = user?.google_connected

  return (
    <div className="page">
      {/* Google Integration Card */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="card-dot" />
            Google Integration
            <span className={`status-badge ${connected ? 'status-connected' : 'status-disconnected'}`}>
              {connected ? '● Connected' : '○ Not connected'}
            </span>
          </div>
        </div>

        <p style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: 20 }}>
          Connect your Google account to automatically create tasks from Gmail emails and sync your schedule to Google Calendar. Smart Scheduler reads your inbox for action items and deadline-related emails, then creates tasks automatically. Your schedule is pushed to Calendar with colour-coded priority events and reminders.
        </p>

        {!connected ? (
          <button className="btn-google" onClick={connectGoogle}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Connect Google Account
          </button>
        ) : (
          <div className="integration-actions">
            <div className="integration-action-card">
              <div className="ia-icon">📧</div>
              <div className="ia-info">
                <div className="ia-title">Sync Gmail → Tasks</div>
                <div className="ia-desc">Scans your last 50 unread emails. Emails with action keywords (deadline, urgent, review, submit…) are automatically converted into tasks with detected priority and deadline.</div>
              </div>
              <button className="btn-accent" onClick={handleGmailSync} disabled={syncing}>
                {syncing ? 'Syncing…' : 'Sync Now'}
              </button>
            </div>

            <div className="integration-action-card">
              <div className="ia-icon">📅</div>
              <div className="ia-info">
                <div className="ia-title">Push Schedule → Google Calendar</div>
                <div className="ia-desc">Pushes all your scheduled (non-completed) tasks to Google Calendar as events with priority colour coding and email + popup reminders. Existing events are updated, not duplicated.</div>
              </div>
              <button className="btn-accent" onClick={handleCalendarPush} disabled={pushing}>
                {pushing ? 'Pushing…' : 'Push to Calendar'}
              </button>
            </div>

            <button className="btn-danger" onClick={handleDisconnect} style={{ marginTop: 12 }}>
              Disconnect Google
            </button>
          </div>
        )}

        {status && (
          <div className={`status-box ${status.startsWith('✅') ? 'status-ok' : status.startsWith('❌') ? 'status-err' : ''}`}>
            <pre style={{ margin: 0, fontFamily: 'inherit', whiteSpace: 'pre-wrap', fontSize: 13 }}>{status}</pre>
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="card">
        <div className="card-title"><span className="card-dot" />How Gmail Sync Works</div>
        <div className="how-it-works">
          {[
            ['🔍 Scan', 'Smart Scheduler reads your last 50 unread inbox emails using the Gmail API (read-only access).'],
            ['🧠 Detect', 'Emails containing keywords like "deadline", "urgent", "please complete", "review by", "submit" etc. are flagged as potential tasks.'],
            ['📋 Extract', 'The subject line becomes the task name. Priority is detected from urgency words. Deadline dates are parsed from email text.'],
            ['✅ Create', 'Tasks are created with source="gmail" so you can see which tasks came from email. Already-synced emails are never duplicated.'],
            ['📅 Calendar', 'After running Gmail sync, push your schedule to Google Calendar. All tasks with a schedule slot become colour-coded calendar events.'],
          ].map(([title, desc]) => (
            <div key={title} className="how-step">
              <div className="how-step-title">{title}</div>
              <div className="how-step-desc">{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
