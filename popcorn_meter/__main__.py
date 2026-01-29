import subprocess
import sys
from pathlib import Path

def main() -> None:
    app_path = Path(__file__).parent / "ui" / "streamlit_app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=False
    )

if __name__ == "__main__":
    main()
