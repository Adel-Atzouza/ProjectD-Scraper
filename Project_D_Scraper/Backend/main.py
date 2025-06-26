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

# Configuration constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Current script directory
DB_FILE = os.path.join(BASE_DIR, "websites.json")      # Website database file
PROGRESS_FOLDER = "progress"                            # Progress tracking folder
SCRAPER_SCRIPT = "Crawlscraper.py"                    # Main scraper script

# Ensure progress folder exists
os.makedirs(PROGRESS_FOLDER, exist_ok=True)

# Global dictionary to track running scraping jobs
running_jobs = {}


# Pydantic models for API request/response validation
class Website(BaseModel):
    """Model for website data with ID and URL"""
    id: int
    url: HttpUrl


class WebsiteCreate(BaseModel):
    """Model for creating a new website entry"""
    url: HttpUrl


class ScrapeRequest(BaseModel):
    """Model for initiating scraping requests with multiple URLs"""
    urls: List[HttpUrl]


def load_db(path: str) -> List[dict]:
    """
    Load website database from JSON file
    
    Args:
        path: Path to the JSON database file
        
    Returns:
        List of website dictionaries, empty list if file doesn't exist
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_db(path: str, data: List[dict]):
    """
    Save website database to JSON file
    
    Args:
        path: Path to the JSON database file
        data: List of website dictionaries to save
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Load website database on startup
db_websites = load_db(DB_FILE)

# Initialize FastAPI application
app = FastAPI()

# Configure CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Allow all origins in development
    allow_credentials=True,       # Allow credentials
    allow_methods=["*"],         # Allow all HTTP methods
    allow_headers=["*"],         # Allow all headers
)


@app.get("/health")
def health():
    """Health check endpoint to verify API is running"""
    return {"status": "alive"}


@app.get("/websites", response_model=List[Website])
def get_websites():
    """
    Get all websites from the database
    
    Returns:
        List of valid websites (filters out entries without URLs)
    """
    # Filter out websites without valid URLs
    valid = [w for w in db_websites if w.get("url")]
    return valid


@app.post("/websites", response_model=Website)
def add_website(website: WebsiteCreate):
    """
    Add a new website to the database
    
    Args:
        website: Website data to add
        
    Returns:
        Created website with assigned ID
        
    Raises:
        HTTPException: If website already exists
    """
def add_website(website: WebsiteCreate):
    """
    Add a new website to the database
    
    Args:
        website: Website data to add
        
    Returns:
        Created website with assigned ID
        
    Raises:
        HTTPException: If website already exists
    """
    # Check if website already exists
    for w in db_websites:
        if str(website.url) == str(w["url"]):
            raise HTTPException(status_code=400, detail="Website already exists")
        continue
    
    # Generate new ID (max existing ID + 1)
    new_id = max([w["id"] for w in db_websites], default=0) + 1
    new_entry = {"id": new_id, "url": str(website.url)}
    
    # Add to database and save
    db_websites.append(new_entry)
    save_db(DB_FILE, db_websites)
    return new_entry


@app.delete("/websites/{website_id}")
def delete_website(website_id: int):
    """
    Delete a website by ID
    
    Args:
        website_id: ID of the website to delete
        
    Returns:
        Deletion confirmation with website details
        
    Raises:
        HTTPException: If website not found
    """
    for w in db_websites:
        if w["id"] == website_id:
            db_websites.remove(w)
            save_db(DB_FILE, db_websites)
            return {"detail": "Website removed", "id": website_id, "url": w["url"]}
    raise HTTPException(status_code=404, detail="Website not found")


@app.get("/stats")
def get_stats():
    """
    Get scraping statistics and metrics
    
    Returns:
        Dictionary with total websites, active jobs, completed jobs, and success rate
    """
    websites = load_db(DB_FILE)
    website_urls = set([w["url"].rstrip("/") for w in websites])
    total = len(websites)

    # Initialize counters
    completed = 0
    active = 0
    relevant_jobs = 0
    total_success = 0
    total_failed = 0

    # Analyze progress files for statistics
    for fname in os.listdir(PROGRESS_FOLDER):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(PROGRESS_FOLDER, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("url", "").rstrip("/")
                
                # Only count jobs for websites in our database
                if url in website_urls:
                    relevant_jobs += 1
                    if data.get("status") == "done":
                        completed += 1
                    if data.get("status") in ("done", "stopped", "scraping"):
                        total_success += data.get("success", 0)
                        total_failed += data.get("failed", 0)
                    elif data.get("status") == "scraping":
                        active += 1
        except Exception:
            continue

    # Calculate success rate
    denom = total_success + total_failed
    success_rate = f"{(total_success / denom * 100):.0f}%" if denom > 0 else "0%"

    return {
        "total": total,
        "active": active,
        "completed": completed,
        "success_rate": success_rate,
    }




@app.get("/activity")
def get_activity():
    """
    Get current activity and job status
    
    Returns:
        Dictionary with list of all job entries and their current status
    """
    entries = []
    
    # Read all progress files
    for fname in os.listdir(PROGRESS_FOLDER):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(PROGRESS_FOLDER, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Use filename as job_id (without .json extension)
                job_id = fname.replace(".json", "")
                entries.append(
                    {
                        "job_id": job_id,
                        "url": data.get("url", "Unknown URL"),
                        "status": data.get("status", "unknown"),
                        "progress": data.get("progress", 0),
                        "done": data.get("done", 0),
                        "total": data.get("total", 0),
                        "success": data.get("success", 0),
                        "failed": data.get("failed", 0),
                        "timestamp": data.get("timestamp", "Unknown time"),
                    }
                )
        except Exception:
            continue
    return {"entries": entries}


@app.delete("/activity/{job_id}")
def delete_activity(job_id: str):
    """
    Delete a specific activity/job and its progress file
    
    Args:
        job_id: ID of the job to delete
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If activity not found or deletion fails
    """
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    if os.path.exists(progress_file):
        try:
            # Remove progress file
            os.remove(progress_file)
            
            # Terminate running process if exists
            if job_id in running_jobs:
                running_jobs[job_id].terminate()
                del running_jobs[job_id]
            return {"detail": f"Activity {job_id} deleted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")
    raise HTTPException(status_code=404, detail="Activity not found")


@app.get("/runs")
def list_runs():
    """
    List all available scraping runs by date
    
    Returns:
        Dictionary with sorted list of run dates (most recent first)
    """
    if not os.path.isdir("output"):
        return {"runs": []}
    dates = sorted(os.listdir("output"), reverse=True)
    return {"runs": dates}


@app.get("/output/{date}")
def get_output_for_date(date: str):
    """
    Get output files for a specific date
    
    Args:
        date: Date string (YYYY-MM-DD format)
        
    Returns:
        Dictionary with sorted list of output files for the date
        
    Raises:
        HTTPException: If date directory not found
    """
    path = os.path.join("output", date)
    if not os.path.isdir(path):
        raise HTTPException(status_code=404, detail="Date not found")
    return {"entries": sorted(os.listdir(path))}


@app.get("/output/{date}/{filename}")
def get_output_file(date: str, filename: str):
    """
    Download a specific output file
    
    Args:
        date: Date string (YYYY-MM-DD format)
        filename: Name of the output file
        
    Returns:
        File response with JSON content
        
    Raises:
        HTTPException: If file not found
    """
    full_path = os.path.join("output", date, filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path, media_type="application/json")


@app.post("/start-scrape")
def start_scrape(request: ScrapeRequest):
    """
    Start scraping jobs for multiple URLs
    
    Args:
        request: Scrape request containing list of URLs to scrape
        
    Returns:
        Dictionary with list of created job IDs and URLs
        
    Raises:
        HTTPException: If URL not in database or subprocess creation fails
    """
    job_ids = []
    
    for url in request.urls:
        # Verify URL exists in database
        if not any(w["url"].rstrip("/") == str(url).rstrip("/") for w in db_websites):
            raise HTTPException(status_code=400, detail=f"URL not in database: {url}")

        # Generate unique job ID
        job_id = str(uuid.uuid4())
        progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")

        # Initialize progress tracking
        log_progress(progress_file, 0, "starting", url=str(url))

        try:
            # Start scraper subprocess
            proc = subprocess.Popen(["python", SCRAPER_SCRIPT, str(url), job_id])
            running_jobs[job_id] = proc
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        job_ids.append({"url": str(url), "job_id": job_id})

    return {"jobs": job_ids}


@app.post("/stop-scrape")
def stop_scrape():
    """
    Stop all running scraping jobs
    
    Returns:
        Dictionary with list of stopped job IDs
    """
    stopped = []
    
    # Terminate all running processes
    for job_id, proc in list(running_jobs.items()):
        proc.terminate()
        
        # Update progress file to mark as stopped
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
    """
    Get progress information for a specific scraping job
    
    Args:
        job_id: ID of the job to check progress for
        
    Returns:
        JSON response with current progress data
        
    Raises:
        HTTPException: If job not found
    """
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    if not os.path.exists(progress_file):
        raise HTTPException(status_code=404, detail="Job not found")
    
    with open(progress_file, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))
