from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import uvicorn

from schemas import ExtractionRequest, ProductData, QuestionRequest
from extractor import extract_product_data
from database import init_db, save_snapshot, get_all_snapshots
from rag_engine import index_product, ask_price_assistant
from notifier import check_and_send_alert

load_dotenv(".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PricePulse AI API",
    description="Self-healing web extraction and RAG price-intelligence backend.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/track", response_model=ProductData)
def track_product(request: ExtractionRequest):
    try:
        product = extract_product_data(str(request.url))
        save_snapshot(product)
        index_product(product)

        alert_sent = False
        if request.target_price is not None:
            alert_sent = check_and_send_alert(product, request.target_price)

        return product.model_copy(update={"alert_sent": alert_sent})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tracking failed: {exc}") from exc


@app.get("/history")
def read_history(limit: int = 50):
    return {"snapshots": get_all_snapshots(limit=limit)}


@app.post("/ask")
def ask_assistant(request: QuestionRequest):
    try:
        answer, sources = ask_price_assistant(request.question)
        return {"question": request.question, "answer": answer, "sources": sources}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {exc}") from exc


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
