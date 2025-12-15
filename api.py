from fastapi import FastAPI, HTTPException
import json, os

app = FastAPI(title="MBA Colleges API")

DATA_FILE = "mba_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.get("/")
async def root():
    return {"message": "API is running! Go to /mba_colleges to see all colleges."}

@app.get("/mba_colleges")
async def get_all_colleges():
    return {"mba_colleges": load_data()}

@app.get("/mba_colleges/{college_id}")
async def get_college_by_id(college_id: int):
    data = load_data()
    idx = 1
    for section in data:
        for college in section["colleges"]:
            if idx == college_id:
                return college
            idx += 1
    raise HTTPException(status_code=404, detail="College not found")
