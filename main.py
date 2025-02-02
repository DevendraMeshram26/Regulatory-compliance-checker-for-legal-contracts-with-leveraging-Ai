import subprocess
import sys
import time
import webbrowser
from threading import Thread
import os

def run_backend():
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Backend stopped by user")

def run_frontend():
    try:
        # Remove the browser opening from Streamlit
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", 
             "app/frontend/app.py", "--server.port", "8501",
             "--server.headless", "true"],  # Prevent automatic browser opening
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting frontend: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Frontend stopped by user")

def open_browser():
    time.sleep(3)  # Wait for servers to start
    try:
        webbrowser.open("http://localhost:8501")
    except Exception as e:
        print(f"Error opening browser: {e}")

if __name__ == "__main__":
    print("Starting Regulatory Compliance Checker...")
    
    # Start backend in a separate thread
    backend_thread = Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Start browser opener in a separate thread
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run frontend in main thread
    print("Starting frontend...")
    run_frontend() 