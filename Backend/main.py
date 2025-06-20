import os
import json
import uuid
import subprocess
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from typing import List, Union
from pydantic import BaseModel

DB_FILE = "websites.json"
PROGRESS_FOLDER = "progress"
SCRAPER_SCRIPT = "CrawlscraperA.py" 

os.makedirs(PROGRESS_FOLDER, exist_ok=True)

class Website(BaseModel):
    id: int
    url: str

class WebsiteCreate(BaseModel):
    url: str

class ScrapeRequest(BaseModel):
    urls: List[str]

try:
    with open("websites.json", "r", encoding="utf-8") as f:
        websites_list = json.load(f)
except FileNotFoundError:
    websites_list = []

running_jobs = {}

app = FastAPI()

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db_websites = json.load(f)
else:
    db_websites = []


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_websites, f, indent=2, ensure_ascii=False)



@app.get("/websites", response_model=List[Website])
def get_websites():
    return db_websites

@app.get("/stats")
def get_stats():
    total = len(db_websites)
    # For demo: completed = files in progress folder not 'started'; active job count is 0 currently
    completed = sum(1 for fname in os.listdir(PROGRESS_FOLDER)
                    if json.load(open(os.path.join(PROGRESS_FOLDER, fname)))["status"] == "completed")
    active = sum(1 for fname in os.listdir(PROGRESS_FOLDER)
                 if json.load(open(os.path.join(PROGRESS_FOLDER, fname)))["status"] == "started")
    success_rate = f"{(completed / total * 100):.0f}%" if total > 0 else "0%"
    return {"total":total, "active":active, "completed":completed, "success_rate":success_rate}


@app.post("/websites", response_model=Website)
def add_website(website: WebsiteCreate):
    new_id = max([w["id"] for w in db_websites], default=0) + 1
    new_entry = {"id": new_id, "url": website.url}
    db_websites.append(new_entry)
    save_db()
    return new_entry


@app.delete("/websites")
def delete_website(url: str):
    if url in db_websites:
        db_websites.remove(url)
        save_db()
        return {"detail": "Website removed", "url": url}
    else:
        raise HTTPException(status_code=404, detail="Website not found")


@app.delete("/websites/{website_id}")
def delete_website(website_id: int):
    for w in db_websites:
        if w["id"] == website_id:
            db_websites.remove(w)
            save_db()
            return {"detail": "Website removed", "id": website_id, "url": w["url"]}

    raise HTTPException(status_code=404, detail="Website not found")

def normalize_url(u: str) -> str:
    return u.rstrip("/").lower()

@app.post("/start-scrape")
def start_scrape(request: ScrapeRequest):
    job_ids = []

    for url in request.urls:
        if not any(w["url"].rstrip("/").lower() == url.rstrip("/").lower() for w in db_websites):
            available = [w["url"] for w in db_websites]
            raise HTTPException(
                status_code=400,
                detail=f'URL not in website list: {url!r}. Available URLs: {available}'
            )

        job_id = str(uuid.uuid4())
        progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")

        with open(progress_file, "w") as f:
            json.dump({
                "progress": 0,
                "status": "started",
                "timestamp": time.time()
            }, f)

        proc = subprocess.Popen(["python", SCRAPER_SCRIPT, url, job_id])
        running_jobs[job_id] = proc

        job_ids.append({"url": url, "job_id": job_id})

    return {"jobs": job_ids}


@app.post("/stop-scrape")
def stop_scrape():
    stopped = []
    for job_id, proc in list(running_jobs.items()):
        proc.terminate()
        # ✅ update progress file
        progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
        if os.path.exists(progress_file):
            with open(progress_file, "r+") as f:
                try:
                    data = json.load(f)
                    data["status"] = "stopped"
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
                except Exception:
                    pass

        stopped.append(job_id)
        del running_jobs[job_id]
    return {"stopped": stopped}


@app.get("/scrape-progress/{job_id}")
def scrape_progress(job_id: str):
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    if not os.path.exists(progress_file):
        raise HTTPException(status_code=404, detail="Job not found")
    
    with open(progress_file, "r") as f:
        progress_data = json.load(f)
    
    return JSONResponse(content=progress_data)
