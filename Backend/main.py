import os
import json
import uuid
import subprocess
from fastapi import FastAPI, HTTPException
from starlette.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel, HttpUrl
from utils import log_progress

# Configuratie via omgevingsvariabelen
DB_FILE = os.getenv("DB_FILE", "websites.json")
PROGRESS_FOLDER = os.getenv("PROGRESS_FOLDER", "progress")
SCRAPER_SCRIPT = os.getenv("SCRAPER_SCRIPT", "CrawlscraperA.py")
API_KEY = os.getenv("API_KEY", "my-secret-key")

# Maak progress folder aan
os.makedirs(PROGRESS_FOLDER, exist_ok=True)

# Houd lopende processen bij
running_jobs = {}


# Pydantic modellen
class Website(BaseModel):
    id: int
    url: HttpUrl


class WebsiteCreate(BaseModel):
    url: HttpUrl


class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]


# Database functies
def load_db(path: str) -> List[dict]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_db(path: str, data: List[dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Laad database
db_websites = load_db(DB_FILE)

# Start FastAPI app
app = FastAPI()

# CORS configuratie
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints
@app.get("/health")
def health():
    return {"status": "alive"}


@app.get("/websites", response_model=List[Website])
def get_websites():
    return db_websites


@app.post("/websites", response_model=Website)
def add_website(website: WebsiteCreate):
    new_id = max([w["id"] for w in db_websites], default=0) + 1
    new_entry = {"id": new_id, "url": str(website.url)}
    db_websites.append(new_entry)
    save_db(DB_FILE, db_websites)
    return new_entry


@app.delete("/websites/{website_id}")
def delete_website(website_id: int):
    for w in db_websites:
        if w["id"] == website_id:
            db_websites.remove(w)
            save_db(DB_FILE, db_websites)
            return {"detail": "Website removed", "id": website_id, "url": w["url"]}
    raise HTTPException(status_code=404, detail="Website not found")


@app.get("/stats")
def get_stats():
    websites = load_db(DB_FILE)
    total = len(websites)

    completed = sum(
        1
        for fname in os.listdir(PROGRESS_FOLDER)
        if fname.endswith(".json")
        and json.load(open(os.path.join(PROGRESS_FOLDER, fname)))["status"] == "done"
    )
    active = sum(
        1
        for fname in os.listdir(PROGRESS_FOLDER)
        if fname.endswith(".json")
        and json.load(open(os.path.join(PROGRESS_FOLDER, fname)))["status"]
        == "scraping"
    )
    success_rate = f"{(completed / total * 100):.0f}%" if total > 0 else "0%"
    return {
        "total": total,
        "active": active,
        "completed": completed,
        "success_rate": success_rate,
    }


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
                entries.append(
                    {
                        "url": data.get("url", "Unknown URL"),
                        "status": data.get("status", "unknown"),
                        "progress": data.get("progress", 0),
                        "done": data.get("done", 0),
                        "total": data.get("total", 0),
                        "success": data.get("success", 0),
                        "failed": data.get("failed", 0),
                    }
                )
        except Exception:
            continue
    return {"entries": entries}


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
        raise HTTPException(status_code=404, detail="Date not found")
    return {"entries": sorted(os.listdir(path))}


@app.get("/output/{date}/{filename}")
def get_output_file(date: str, filename: str):
    full_path = os.path.join("output", date, filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path, media_type="application/json")


@app.post("/start-scrape")
def start_scrape(request: ScrapeRequest):
    job_ids = []
    for url in request.urls:
        if not any(w["url"].rstrip("/") == str(url).rstrip("/") for w in db_websites):
            raise HTTPException(status_code=400, detail=f"URL not in database: {url}")

        job_id = str(uuid.uuid4())
        progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")

        log_progress(progress_file, 0, "starting", url=str(url))

        try:
            proc = subprocess.Popen(["python", SCRAPER_SCRIPT, str(url), job_id])
            running_jobs[job_id] = proc
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        job_ids.append({"url": str(url), "job_id": job_id})

    return {"jobs": job_ids}


@app.post("/stop-scrape")
def stop_scrape():
    stopped = []
    for job_id, proc in list(running_jobs.items()):
        proc.terminate()
        progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
        if os.path.exists(progress_file):
            with open(progress_file, "r+", encoding="utf-8") as f:
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
    with open(progress_file, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))
