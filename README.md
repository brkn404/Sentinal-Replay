# Job Progress Simulator Dashboard

A real-time dashboard for visualizing job throughput and progress from log files. Features a live-updating line plot of Bytes/sec (throughput) for each backup set, with a clean executive-style UI.

## Features
- Enter a job ID to simulate and visualize its progress
- Live plot of Bytes/sec (throughput) for each backup set
- Modern, responsive dashboard UI
- Works with your log file format (JSON lines)
- Fast simulation and real-time updates

## Setup (Portable)

1. **Clone or copy this directory to any machine with Python 3.7+**

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Place your log file** (e.g., `parselogs.xxxxxx.jobprog.log.out`) in the project directory.

5. **Run the app:**
   ```bash
   python app.py
   ```

6. **Open your browser:**
   Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Usage
- Enter a job ID and click "Start Simulation".
- The dashboard will replay the log for that job, showing a live plot of throughput (Bytes/sec).
- You can experiment with different jobs or log files by restarting the simulation.

## Portability
- No system-wide dependencies required; everything runs in a Python virtual environment.
- All static assets (HTML, JS, CSS) are included.
- Works on macOS, Linux, and Windows (with Python 3.7+).

## Customization
- To change the log file name, edit the `log_file` variable in `app.py`.
- To adjust the simulation speed, change the `time.sleep` value in `app.py`.
- To add more metrics or plots, edit `templates/index.html` and the backend logic in `app.py`.

## Requirements
- Python 3.7+
- See `requirements.txt` for Python package dependencies

## License
MIT License (or specify your own) 