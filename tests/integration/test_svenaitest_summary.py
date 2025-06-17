import os
import subprocess


def test_svenai_generates_summary():
    test_dir = os.path.dirname(__file__)
    script_path = os.path.abspath(os.path.join(test_dir, "../../AI/SvenAitest.py"))

    if os.path.exists("samenvatting.txt"):
        os.remove("samenvatting.txt")

    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    assert result.returncode == 0, f"AI-summary faalde: {result.stderr}"

    assert os.path.exists("samenvatting.txt"), "samenvatting.txt is niet aangemaakt"
