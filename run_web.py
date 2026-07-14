import subprocess
import sys
from pathlib import Path


def main():
    app_path = Path(__file__).parent / "src" / "web" / "app.py"
    print(f"Starting ResearchAgent Web UI...")
    print(f"App: {app_path}")
    print()

    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    main()
