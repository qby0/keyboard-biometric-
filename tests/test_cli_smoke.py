import json
import subprocess
import sys


def run_ok(args):
    proc = subprocess.run([sys.executable, "-m", "persona_by_text", *args], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_help():
    out = run_ok(["--help"])
    assert "train" in out and "ks-train" in out
