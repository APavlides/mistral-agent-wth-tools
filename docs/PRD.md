# PRD: Order support agent with tools

## Goal

A chat where Mistral answers order questions by calling Python functions over fake in-memory data.

## User

A customer (or the interviewer) asking about an order in plain English, e.g. "Where is order A123?".

## Core flow

1. User types a message in the React chat and sends it.
2. Frontend POSTs the conversation to `/api/chat` (via the Vite proxy).
3. Backend sends the messages plus tool schemas to Mistral.
4. If Mistral returns tool calls, the backend runs the matching Python function(s), appends the results as `tool` messages, and calls Mistral again (loop, max ~5 rounds).
5. Backend returns the final assistant reply, plus which tools were called.
6. Frontend shows the reply (and a small "called get_order_status(A123)" note).

## Out of scope

Database, auth, Docker, tests, styling, streaming, real order systems, write actions (cancel/refund), multi-user sessions, persisting chat history server-side, Mistral Agents API (we use plain chat completions + tools).

## Endpoints and data

- `GET /api/health` (exists).
- `POST /api/chat`: request `{ messages: [{role, content}] }` → response `{ reply: str, tool_calls: [{name, args, result}] }`. Stateless: the frontend sends full history.
- In-memory `ORDERS` dict in `main.py`: `order_id → {status, items, eta, customer}` (~4 fake orders).
- Tools: `get_order_status(order_id)`, plus one more (see Open questions).

## Milestones

- [x] **M1 Thin slice (stubbed)**: `POST /api/chat` returns an echo; minimal chat UI calls it. _Done when:_ typing a message in the browser shows the echo reply.
- [x] **M2 Real Mistral chat**: shared async client in lifespan, no tools yet. _Done when:_ curl and UI get a real Mistral reply.
- [x] **M3 One tool**: `ORDERS` data + `get_order_status` schema + tool-call loop. _Done when:_ "Where is order A123?" returns the fake status from `ORDERS`.
- [x] **M4 Second tool + tool trace**: add second tool; response includes `tool_calls`, UI shows them. _Done when:_ a question that needs the second tool works and the UI shows which tools ran.
- [x] **M5 Edge cases**: unknown order ID returns a clear tool result (`{"error": "not found"}`); max-rounds guard on the loop. _Done when:_ " ZZZ?" gets a polite "can't find it" reply, no crash.
- [ ] **M6 Hardening**: SDK timeout + retry config (429/5xx/timeouts); map errors to 429 / 502 / 504. _Done when:_ a bad API key gives a clear 502 in curl and an error state in the UI.

## Open questions

1. **What is the second tool?** Decided: `list_orders_by_customer(email)`, so the agent can chain into `get_order_status`.
2. **Should the UI show tool calls to the user?** Decided: yes, a small grey line per call.
3. **Stateless or server-side history?** Decided: stateless, the frontend sends the full message list each turn.
