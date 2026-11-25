from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel

from chatbot_rag.llm import answer
from chatbot_rag.retriever import Retriever

api = FastAPI()
retriever = Retriever()

class ChatRequest(BaseModel):
    question: str

class Source(BaseModel):
    source: str
    page: int
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]

@api.get("/health")
def health():
    return {"status": "ok"}

@api.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    chunks = retriever.search(req.question)
    response = answer(req.question, chunks)

    return ChatResponse(
        answer=response,
        sources=[
            Source(
                source=c["source"],
                page=c["page"],
                score=round(c["score"], 3)
            ) for c in chunks
        ],
    )