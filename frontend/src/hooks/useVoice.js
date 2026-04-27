import { useState, useRef, useCallback } from 'react'

export function useVoice({ onResult, onEnd }) {
  const [listening, setListening] = useState(false)
  const [supported] = useState(() => !!(window.SpeechRecognition || window.webkitSpeechRecognition))
  const recRef = useRef(null)

  const start = useCallback(() => {
    if (!supported || listening) return
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const rec = new SR()
    rec.lang = 'en-IN'
    rec.continuous = false
    rec.interimResults = true

    rec.onstart = () => setListening(true)
    rec.onresult = (e) => {
      let final = '', interim = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript
        else interim += e.results[i][0].transcript
      }
      onResult?.(final || interim, !!final)
    }
    rec.onend = () => { setListening(false); onEnd?.() }
    rec.onerror = () => setListening(false)

    recRef.current = rec
    rec.start()
  }, [supported, listening, onResult, onEnd])

  const stop = useCallback(() => {
    recRef.current?.stop()
    setListening(false)
  }, [])

  const speak = useCallback((text) => {
    if (!window.speechSynthesis || !text) return
    window.speechSynthesis.cancel()
    const utt = new SpeechSynthesisUtterance(text.substring(0, 280))
    utt.rate = 0.95; utt.pitch = 1; utt.volume = 0.9
    const voices = window.speechSynthesis.getVoices()
    const v = voices.find(v => v.lang === 'en-IN') || voices.find(v => v.lang.startsWith('en'))
    if (v) utt.voice = v
    window.speechSynthesis.speak(utt)
  }, [])

  return { listening, supported, start, stop, speak }
}
