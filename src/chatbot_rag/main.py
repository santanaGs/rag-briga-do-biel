from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

api = FastAPI()


@api.get("/health")
def health():
    return {"status": "ok"}
