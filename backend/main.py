import json
import logging
import os
from contextlib import asynccontextmanager

import httpx2 as httpx  # the SDK's HTTP library (a fork of httpx)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from mistralai.client import Mistral
from mistralai.client.errors import MistralError
from mistralai.client.utils import BackoffStrategy, RetryConfig
from pydantic import BaseModel, Field

load_dotenv()
log = logging.getLogger("uvicorn.error")

MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
MAX_TOOL_ROUNDS = 5
TIMEOUT_MS = 30_000

# SDK retries 429/5xx and connection errors with exponential backoff + jitter
RETRY = RetryConfig(
    "backoff",
    BackoffStrategy(initial_interval=500, max_interval=5_000, exponent=2, max_elapsed_time=20_000, jitter_ms=1_000),
    retry_connection_errors=True,
)

# Fake in-memory order data
ORDERS = {
    "A123": {"status": "shipped", "items": ["Blue mug"], "eta": "2026-11-10", "customer": "ana@example.com"},
    "B456": {"status": "processing", "items": ["Desk lamp", "Bulb"], "eta": "2026-11-14", "customer": "ben@example.com"},
    "C789": {"status": "delivered", "items": ["Notebook"], "eta": "2026-11-05", "customer": "ana@example.com"},
    "D012": {"status": "cancelled", "items": ["Headphones"], "eta": None, "customer": "cara@example.com"},
}


def get_order_status(order_id: str) -> dict:
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"error": f"Order {order_id} not found"}
    return {"order_id": order_id.upper(), **order}


def list_orders_by_customer(email: str) -> dict:
    email = email.strip().lower()
    orders = [{"order_id": oid, "status": o["status"]} for oid, o in ORDERS.items() if o["customer"] == email]
    if not orders:
        return {"error": f"No orders found for {email}"}
    return {"email": email, "orders": orders}


# Python functions the model is allowed to call, by name
TOOLS = {"get_order_status": get_order_status, "list_orders_by_customer": list_orders_by_customer}

def run_tool(name: str, raw_args: str | dict) -> tuple[dict, dict]:
    # Never raise: errors go back to the model as a tool result it can explain
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    except json.JSONDecodeError:
        return {}, {"error": "Arguments were not valid JSON"}
    if name not in TOOLS:
        return args, {"error": f"Unknown tool {name}"}
    try:
        return args, TOOLS[name](**args)
    except TypeError as e:
        return args, {"error": f"Bad arguments: {e}"}


# JSON schemas describing those functions to Mistral
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up an order's status, items and ETA by its order ID.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "Order ID, e.g. A123"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders_by_customer",
            "description": "List all order IDs and statuses for a customer, by their email address.",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string", "description": "Customer email, e.g. ana@example.com"}},
                "required": ["email"],
            },
        },
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One shared Mistral client for the whole app, closed on shutdown
    async with Mistral(api_key=os.environ["MISTRAL_API_KEY"], timeout_ms=TIMEOUT_MS, retry_config=RETRY) as client:
        app.state.mistral = client
        yield


app = FastAPI(lifespan=lifespan)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1)


class ToolCall(BaseModel):
    name: str
    args: dict
    result: dict


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCall] = []


@app.get("/api/health")
def health():
    return {"status": "ok"}


async def call_mistral(client: Mistral, messages: list[dict]):
    # Map upstream failures (after SDK retries) to clear HTTP errors
    try:
        return await client.chat.complete_async(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
    except MistralError as e:
        log.warning("Mistral error: status %s", e.status_code)
        if e.status_code == 429:
            raise HTTPException(429, "Rate limited by Mistral, try again shortly")
        raise HTTPException(502, f"Upstream error from Mistral ({e.status_code})")
    except httpx.TimeoutException:
        log.warning("Mistral timed out")
        raise HTTPException(504, "Mistral timed out")
    except httpx.NetworkError:
        log.warning("Could not reach Mistral")
        raise HTTPException(502, "Could not reach Mistral")


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    client: Mistral = request.app.state.mistral
    messages = [m.model_dump() for m in req.messages]
    trace: list[ToolCall] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = await call_mistral(client, messages)
        msg = response.choices[0].message
        if not msg.tool_calls:
            return ChatResponse(reply=msg.content, tool_calls=trace)

        # Keep the assistant's tool request in history, then answer each call
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})
        for call in msg.tool_calls:
            args, result = run_tool(call.function.name, call.function.arguments)
            trace.append(ToolCall(name=call.function.name, args=args, result=result))
            messages.append(
                {"role": "tool", "name": call.function.name, "content": json.dumps(result), "tool_call_id": call.id}
            )

    return ChatResponse(reply="Sorry, I couldn't finish that request.", tool_calls=trace)
