import { useState, useRef, useEffect } from 'react'
import { askAI } from '../services/api'
import { useVoice } from '../hooks/useVoice'

const QUICK = [
  "What should I focus on today?",
  "When is my best work hour?",
  "Give me my weekly insights summary",
  "Which tasks are overdue?",
  "How can I improve my productivity?",
  "What's on my schedule today?",
]

export default function AIPanel({ open }) {
  const [messages, setMessages] = useState([
    { type: 'bot', text: "Hi! I can help you plan your day, understand your productivity, or turn ideas into tasks. What would you like to do?" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const boxRef = useRef(null)
  const inputRef = useRef(null)

  const { listening, supported, start, stop, speak } = useVoice({
    onResult: (text, isFinal) => {
      setInput(text)
      if (isFinal) setInput(text)
    },
    onEnd: () => {
      // Auto-send after voice
      setTimeout(() => {
        const val = inputRef.current?.value?.trim()
        if (val) send(val)
      }, 200)
    },
  })

  useEffect(() => {
    if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight
  }, [messages])

  const send = async (text) => {
    const q = (text || input).trim()
    if (!q || loading) return
    setInput('')
    setMessages(m => [...m, { type: 'user', text: q }])
    setLoading(true)
    try {
      const r = await askAI(q)
      const { answer, suggested_task } = r.data
      setMessages(m => [...m, { type: 'bot', text: answer, suggestedTask: suggested_task }])
      if (answer.length < 250) speak(answer)
    } catch {
      setMessages(m => [...m, { type: 'bot', text: 'Could not reach AI. Check your connection.' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const useAsTask = (name) => {
    window.dispatchEvent(new CustomEvent('ai-suggest-task', { detail: name }))
  }

  if (!open) return null

  return (
    <aside className="ai-panel">
      <div className="ai-panel-head">
        <div className="ai-panel-title">
          <span className="ai-dot" />
          AI Assistant
        </div>
        <span className="ai-status-badge">{loading ? 'Thinking…' : listening ? '🔴 Listening' : 'Ready'}</span>
      </div>

      <div className="chat-box" ref={boxRef}>
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.type}`}>
            {m.text}
            {m.suggestedTask && (
              <div>
                <button className="use-task-btn" onClick={() => useAsTask(m.suggestedTask)}>
                  ↗ Use as task: {m.suggestedTask}
                </button>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="msg bot">
            <div className="typing"><span /><span /><span /></div>
          </div>
        )}
      </div>

      <div className="ai-input-area">
        <div className="ai-input-row">
          <textarea
            ref={inputRef}
            className="ai-text-input"
            value={input}
            onChange={e => { setInput(e.target.value); e.target.style.height = '38px'; e.target.style.height = Math.min(e.target.scrollHeight, 90) + 'px' }}
            onKeyDown={handleKey}
            placeholder="Ask about tasks, focus, schedule…"
            rows={1}
          />
          {supported && (
            <button
              className={`btn-voice${listening ? ' recording' : ''}`}
              onClick={listening ? stop : start}
              title={listening ? 'Stop listening' : 'Hold to speak'}
            >
              🎤
            </button>
          )}
          <button className="btn-send-ai" onClick={() => send()} disabled={loading}>↑</button>
        </div>
        {listening && <div className="voice-status active">🔴 Listening… speak now</div>}

        <div className="ai-quick-btns">
          {QUICK.map(q => (
            <button key={q} className="quick-btn" onClick={() => send(q)}>{q}</button>
          ))}
        </div>
      </div>
    </aside>
  )
}
