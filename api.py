from fastapi import FastAPI
import json

app = FastAPI(title="MBA Colleges API")

@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/mba_colleges")
def mba_colleges():
    with open("mba_data.json", "r", encoding="utf-8") as f:
        return {"mba_colleges": json.load(f)}
