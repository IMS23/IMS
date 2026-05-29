import sys
import os
import subprocess
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def start_ollama():
    """Start ollama serve in background if not already running."""
    import urllib.request
    # Check if already running
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        print("[Ollama] Already running.")
        return
    except:
        pass
    # Start it
    print("[Ollama] Starting ollama serve...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        # Wait up to 8 seconds for it to come up
        for _ in range(16):
            time.sleep(0.5)
            try:
                urllib.request.urlopen("http://localhost:11434", timeout=1)
                print("[Ollama] Ready.")
                return
            except:
                continue
        print("[Ollama] Started but not yet responding — continuing anyway.")
    except FileNotFoundError:
        print("[Ollama] ollama not found in PATH — AI panel will show offline.")
    except Exception as e:
        print(f"[Ollama] Could not start: {e}")


def main():
    # Start Ollama in background thread so UI doesn't freeze
    t = threading.Thread(target=start_ollama, daemon=True)
    t.start()

    app = QApplication(sys.argv)
    app.setApplicationName("MIDI Composer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
