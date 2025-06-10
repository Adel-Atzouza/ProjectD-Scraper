import os
import subprocess


def test_playwright_scraper_creates_output():
    test_dir = os.path.dirname(__file__)
    script_path = os.path.abspath(os.path.join(test_dir, "../../AI/test.py"))

    if not os.path.exists("files"):
        os.makedirs("files")

    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    assert result.returncode == 0, f"Playwright script faalde: {result.stderr}"

    files = os.listdir("files")
    assert any(
        f.endswith(".txt") for f in files
    ), "Geen .txt bestanden gevonden in files/"
