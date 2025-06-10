import os
import subprocess


def test_main_creates_files():
    test_dir = os.path.dirname(__file__)
    main_script = os.path.abspath(os.path.join(test_dir, "../../AI/main.py"))

    if not os.path.exists("files"):
        os.makedirs("files")

    result = subprocess.run(["python", main_script], capture_output=True, text=True)
    assert result.returncode == 0, f"main.py faalde: {result.stderr}"

    files = os.listdir("files")
    assert any(
        f.endswith(".txt") for f in files
    ), "Geen .txt bestanden gevonden in files/"
