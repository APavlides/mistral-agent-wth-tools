# Practice starter

A minimal FastAPI and React app to build AI features on. It has a health check and nothing else.

## 1. What's here

| Folder | What it does |
|---|---|
| `backend/` | Python API (FastAPI), managed by **uv**. It runs on port 8000. Mistral calls go here, because the API key must stay on the server. |
| `frontend/` | Web page (React + TypeScript), built and served by **Vite** and managed by **pnpm**. It runs on port 5173 and calls the backend through `/api/...`. |

## 2. Prerequisites

Check what you have:

```bash
python3 --version   # needs 3.12+ (uv can also download Python for you)
uv --version
node --version      # needs 20.19+ or 22.12+ for current Vite
pnpm --version
```

Install whatever is missing:

```bash
brew install python@3.12 uv node pnpm
```

If `node --version` still shows an old version after `brew install node`, you probably also have **nvm** (a Node version manager) and its Node comes first on your PATH. Run `nvm alias default system` to use Homebrew's Node, then open a new terminal.

## 3. Setup (once per clone)

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and paste your key after `MISTRAL_API_KEY=`. Git ignores `.env`, so it never gets committed.

## 4. Running it (3 terminals in VS Code)

Open a terminal with **Ctrl+`** (or Terminal → New Terminal). Add more with the **+** button in the terminal panel. To rename a tab, right-click it and choose **Rename**, e.g. "backend".

**Tab 1: backend**

```bash
cd backend
uv sync                                    # installs Python packages into .venv
uv run uvicorn main:app --reload --port 8000
```

**Tab 2: frontend**

```bash
cd frontend
pnpm install                               # installs JS packages into node_modules
pnpm dev                                   # serves http://localhost:5173
```

**Tab 3: Claude Code** (from the repo root)

```bash
claude
```

Open http://localhost:5173. You should see "Backend: ok".

To **stop** a server, click its tab and press **Ctrl+C**. To **restart** it, press **Up arrow** (recalls the last command), then **Enter**.

## 5. The tools in plain words

| Tool / file | What it is |
|---|---|
| **uv** | The Python tool that does everything: installs Python, creates the virtual environment, adds packages (`uv add x`) and runs commands inside it (`uv run ...`). It replaces pip, venv and pyenv. |
| `pyproject.toml` / `uv.lock` | `pyproject.toml` lists the packages you asked for. `uv.lock` records the exact versions installed, so every machine gets the same ones. Commit both. |
| `.venv/` | The project's private Python install and packages. `uv sync` creates it. Never commit it; you can delete it and rebuild at any time. |
| **FastAPI** | The Python web framework. You write functions and decorate them with `@app.get("/path")` to turn them into URLs. Interactive docs are at http://localhost:8000/docs. |
| **uvicorn** | The server that runs the FastAPI app. `main:app` means "the `app` object in `main.py`". `--reload` restarts it whenever you save a `.py` file. |
| **pnpm** | The JavaScript package manager, a faster npm. `pnpm install` installs packages, `pnpm add x` adds one, and `pnpm dev` runs the `dev` script from `package.json`. |
| `package.json` / `pnpm-lock.yaml` | The same idea as `pyproject.toml` and `uv.lock`, for JavaScript. Commit both. |
| `node_modules/` | The installed JS packages, like `.venv` for JS. Never commit it; `pnpm install` rebuilds it. |
| **Vite** | The frontend dev server and build tool. It serves your React code and updates the browser instantly when you save (hot reload). |
| **Vite proxy** | Set in `vite.config.ts`. The browser asks `localhost:5173/api/...` and Vite forwards the request to `localhost:8000`. The browser only ever talks to one origin, so there's **no CORS** to configure. |
| **React / `.tsx`** | React builds the page from components (functions that return HTML-like JSX). `.tsx` is TypeScript with JSX. The page lives in `frontend/src/App.tsx`. |

## 6. When to restart

| You changed... | What to do |
|---|---|
| A `.py` file | Nothing, `--reload` restarts the backend |
| A `.tsx` / `.css` file | Nothing, Vite updates the browser |
| `backend/.env` | Restart the backend (Ctrl+C, Up, Enter) |
| Added a Python package (`uv add`) | Restart the backend |
| Added a JS package (`pnpm add`) | Usually nothing; restart `pnpm dev` if imports fail |
| `vite.config.ts` | Vite usually restarts itself; if not, restart `pnpm dev` |

## 7. Common problems

| Symptom | Fix |
|---|---|
| `Address already in use` / port 8000 or 5173 busy | An old server is still running. Find it with `lsof -i :8000`, then `kill <PID>` (the number in the PID column). |
| `ModuleNotFoundError` in the backend | Run `uv sync` in `backend/`, and always start the server with `uv run ...`. |
| `vite: command not found` / `sh: vite: not found` | Run `pnpm install` in `frontend/`. |
| `/api/...` gives 404 or a network error, or the page says "Backend: unreachable" | Check the backend is running (`curl localhost:8000/api/health`). If it is, check the proxy in `vite.config.ts` and that the route starts with `/api`. |
| CORS error in the browser console | The frontend is calling `http://localhost:8000/...` directly. Use relative paths like `fetch('/api/...')` so the proxy handles them. |
| Mistral `401 Unauthorized` | Bad or missing key. Check `MISTRAL_API_KEY` in `backend/.env` (no quotes or spaces), then **restart the backend**, because `.env` is only read at startup. |
| Mistral `429 Too Many Requests` | You hit the rate limit (free tiers are low). Wait a few seconds and try again. |
| `uv init --app` made a `src/` folder instead of `main.py` | Newer uv versions package apps by default. Use `uv init <name> --app --no-package`. |
| `pnpm create vite` asks extra questions | Answer them, or add `--no-interactive` to skip them. |
