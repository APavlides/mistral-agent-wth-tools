import { useEffect, useRef, useState } from 'react';

type ToolCall = { name: string; args: Record<string, unknown>; result: Record<string, unknown> }
type Message = { role: 'user' | 'assistant'; content: string; toolCalls?: ToolCall[] }

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Keep the newest message in view
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    const next: Message[] = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send only role + content; the tool trace is for display
        body: JSON.stringify({ messages: next.map(({ role, content }) => ({ role, content })) }),
      })
      if (!res.ok) {
        // Show the backend's error message if it sent one
        const body = await res.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : `Request failed (${res.status})`)
      }
      const data = await res.json()
      setMessages([...next, { role: 'assistant', content: data.reply, toolCalls: data.tool_calls }])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>Order support agent</h1>

      <div className="chat">
        <div className="chat-header">Order support</div>

        <div className="messages">
          {messages.length === 0 && <p className="empty">Ask about an order, e.g. "Where is order A123?"</p>}

          {messages.map((m, i) => (
            <div key={i} className={`turn ${m.role}`}>
              {m.toolCalls?.map((t, j) => (
                <span key={j} className="tool">
                  🔧 {t.name}({JSON.stringify(t.args)})
                </span>
              ))}
              <div className="bubble">{m.content}</div>
            </div>
          ))}

          {loading && <p className="status">Thinking…</p>}
          {error && <p className="error">Error: {error}</p>}
          <div ref={bottomRef} />
        </div>

        <form className="composer" onSubmit={send}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </main>
  )
}

export default App
