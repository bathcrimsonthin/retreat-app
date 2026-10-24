from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 受け取るJSON構造
class DataModel(BaseModel):
    title: str
    minutes: int

@app.post("/api/sessions")
async def create_session(data: DataModel):
    return {"message": "received", "data": data.model_dump() }
    # .model_dump() 辞書形式に変換

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}