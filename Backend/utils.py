import re
import json
import os
from datetime import datetime
from urllib.parse import urlparse

EXCLUDE_EXTENSIONS = [".pdf", ".doc", ".zip", ".rar", ".ppt", ".xlsx"]


def is_excluded(url: str) -> bool:
    path = urlparse(url).path
    return any(path.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)


def clean_text(markdown: str) -> str:
    markdown = re.sub(r"(?m)^.*\|.*\|.*$", "", markdown)
    markdown = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", markdown)
    markdown = re.sub(r"(?m)^#+ .*$", "", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown.strip())
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
):
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
