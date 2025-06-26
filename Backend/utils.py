import re
import json
import os
from datetime import datetime
from urllib.parse import urlparse

# File extensions to exclude from crawling (typically non-content files)
EXCLUDE_EXTENSIONS = [".pdf", ".doc", ".zip", ".rar", ".ppt", ".xlsx"]


def is_excluded(url: str) -> bool:
    """
    Check if a URL should be excluded from crawling based on file extension
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if the URL should be excluded, False otherwise
    """
    path = urlparse(url).path
    return any(path.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)


def clean_text(markdown: str) -> str:
    """
    Clean and process markdown text for better readability and storage
    
    This function removes unwanted elements like tables, headers, and links,
    then limits the output to the first 5 sentences for summary purposes.
    
    Args:
        markdown: Raw markdown text to clean
        
    Returns:
        str: Cleaned and truncated text summary
    """
    # Remove table rows (lines containing multiple | characters)
    markdown = re.sub(r"(?m)^.*\|.*\|.*$", "", markdown)
    
    # Convert markdown links to plain text (keep only the link text)
    markdown = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", markdown)
    
    # Remove markdown headers (lines starting with #)
    markdown = re.sub(r"(?m)^#+ .*$", "", markdown)
    
    # Reduce multiple consecutive newlines to maximum of 2
    markdown = re.sub(r"\n{3,}", "\n\n", markdown.strip())
    
    # Split into sentences and limit to first 5 for summary
    sentences = re.split(r"(?<=[.!?]) +", markdown)
    return " ".join(sentences[:5]).strip()


def log_progress(
    path: str,
    progress: int,
    status: str,
    done: int = 0,
    total: int = 0,
    success: int = 0,
    failed: int = 0,
    url: str = "",
    timestamp: datetime = None,
):
    """
    Log scraping progress to a JSON file for tracking and monitoring
    
    This function creates or updates a progress file with current status,
    completion metrics, and timing information for a scraping job.
    
    Args:
        path: File path where progress should be logged
        progress: Current progress percentage (0-100)
        status: Current status description (e.g., "starting", "scraping", "done")
        done: Number of items completed (default: 0)
        total: Total number of items to process (default: 0)
        success: Number of successful operations (default: 0)
        failed: Number of failed operations (default: 0)
        url: URL being processed (default: "")
        timestamp: Custom timestamp (default: current time)
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "progress": progress,
                "status": status,
                "done": done,
                "total": total,
                "success": success,
                "failed": failed,
                "url": url,
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )