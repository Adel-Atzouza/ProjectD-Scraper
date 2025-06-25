import os
import json
import uuid
import subprocess
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from typing import List, Union
from pydantic import BaseModel, HttpUrl
from fastapi.responses import FileResponse


DB_FILE = "websites.json"
PROGRESS_FOLDER = "progress"
SCRAPER_SCRIPT = "CrawlscraperA.py" 

os.makedirs(PROGRESS_FOLDER, exist_ok=True)

class Website(BaseModel):
    id: int
    url: HttpUrl

class WebsiteCreate(BaseModel):
    url: HttpUrl

class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]

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


@app.delete("/websites/{website_id}")
def delete_website_by_id(website_id: int):
    for w in db_websites:
        if int(w["id"]) == website_id:
            db_websites.remove(w)
            save_db()
            return {"detail": "Website removed", "id": website_id, "url": w["url"]}
    raise HTTPException(status_code=404, detail="Website not found wdwdwdwdwd")


@app.get("/websites", response_model=List[Website])
def get_websites():
    return db_websites


@app.get("/stats")
def get_stats():
    total = len(db_websites)
    # Collect all URLs currently in the DB, normalized
    db_urls = {str(w["url"]).rstrip("/").lower() for w in db_websites}

    completed = 0
    active = 0

    for fname in os.listdir(PROGRESS_FOLDER):
        try:
            with open(os.path.join(PROGRESS_FOLDER, fname)) as f:
                data = json.load(f)
                # Make sure to only count if the URL is in the current DB
                url = str(data.get("url", "")).rstrip("/").lower()
                if url in db_urls:
                    if data.get("status") == "done":
                        completed += 1
                    if data.get("status") == "started":
                        active += 1
        except Exception:
            continue

    success_rate = f"{(completed / total * 100):.0f}%" if total > 0 else "0%"

    return {"total": total, "active": active, "completed": completed, "success_rate": success_rate}



@app.get("/activity")
def get_activity():
    entries = []
    for fname in os.listdir(PROGRESS_FOLDER):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(PROGRESS_FOLDER, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                entry = {
                    "url": data.get("url", "Unknown URL"),
                    "status": data.get("status", "unknown"),
                    "progress": data.get("progress", 0),
                    "done": data.get("done", 0),
                    "total": data.get("total", 0),
                    "success": data.get("success", 0),
                    "failed": data.get("failed", 0),
                }
                entries.append(entry)
        except Exception:
            continue

    return {"entries": entries}


@app.post("/websites", response_model=Website)
def add_website(website: WebsiteCreate):
    norm_new_url = str(website.url).rstrip("/").lower()
    for w in db_websites:
        norm_existing_url = str(w["url"]).rstrip("/").lower()
        if norm_existing_url == norm_new_url:
            raise HTTPException(
                status_code=409,
                detail=f"Website already exists: {website.url}"
            )
    new_id = max([w["id"] for w in db_websites], default=0) + 1
    new_entry = {"id": new_id, "url": str(website.url)}
    db_websites.append(new_entry)
    save_db()
    return new_entry



@app.get("/output/{date}/{filename}")
def get_output_file(date: str, filename: str):
    full_path = os.path.join("output", date, filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path, media_type="application/json")


@app.delete("/websites")
def delete_website(url: str):
    norm_url = str(url).rstrip("/").lower()
    for w in db_websites:
        if str(w["url"]).rstrip("/").lower() == norm_url:
            db_websites.remove(w)
            save_db()
            return {"detail": "Website removed", "url": url}
    raise HTTPException(status_code=404, detail="Website not found")


def normalize_url(u: str) -> str:
    return str(u).rstrip("/").lower()

@app.post("/start-scrape")
def start_scrape(request: ScrapeRequest):
    job_ids = []

    for url in request.urls:
        if not any(str(w["url"]).rstrip("/").lower() == url.rstrip("/").lower() for w in db_websites):
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


@app.get("/runs")
def list_runs():
    if not os.path.isdir("output"):
        return {"runs": []}
    dates = sorted(os.listdir("output"), reverse=True)
    return {"runs": dates}

@app.get("/output/{date}")
def get_output_for_date(date: str):
    path = os.path.join("output", date)
    if not os.path.isdir(path):
        raise HTTPException(404, "Date not found")
    return {"entries": sorted(os.listdir(path))}


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
