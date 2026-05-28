# from Milestone2.backend import app
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "working"}