from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI()


@app.get("/api/health")
def health():
    return {"status": "ok"}
