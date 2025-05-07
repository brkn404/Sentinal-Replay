from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import time
import threading
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

# Store simulation state
simulation_threads = {}

# Helper to parse and filter log lines for a jobid
def get_job_lines_and_max(job_id):
    log_file = "parselogs.lipsgcxap02.jobprog.log.out"
    job_lines = []
    max_sofar_bytes = 0
    max_nfiles = 0
    max_ndirs = 0
    max_total_bytes = 0
    with open(log_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if str(data.get('jobid')) == str(job_id):
                    job_lines.append(data)
                    for bs in data.get('bsProgs', []):
                        for level in bs.get('levels', []):
                            max_sofar_bytes = max(max_sofar_bytes, level.get('sofar_bytes', 0))
                            max_total_bytes = max(max_total_bytes, level.get('total_bytes', 0))
                        max_nfiles = max(max_nfiles, bs.get('nfiles', 0))
                        max_ndirs = max(max_ndirs, bs.get('ndirs', 0))
            except Exception:
                continue
    return job_lines, max_sofar_bytes, max_nfiles, max_ndirs, max_total_bytes

def simulate_job(job_id):
    job_lines, _, _, _, _ = get_job_lines_and_max(job_id)
    if not job_lines:
        socketio.emit('job_update', {'error': f'No data found for jobid {job_id}'})
        return
    # Track previous values for rate calculation per backup set
    prev_vals = {}
    max_rates = {}
    for entry in job_lines:
        updates = []
        nowtm = entry.get('nowtm')
        for bs_idx, bs in enumerate(entry.get('bsProgs', [])):
            for level_idx, level in enumerate(bs.get('levels', [])):
                key = (bs_idx, level_idx)
                prev = prev_vals.get(key)
                # Current values
                curr_sofar = level.get('sofar_bytes', 0)
                curr_nfiles = bs.get('nfiles', 0)
                curr_ndirs = bs.get('ndirs', 0)
                curr_time = nowtm
                # Calculate rates
                if prev:
                    dt = max(1, curr_time - prev['time'])
                    rate_sofar = max(0, (curr_sofar - prev['sofar_bytes']) / dt)
                    rate_nfiles = max(0, (curr_nfiles - prev['nfiles']) / dt)
                    rate_ndirs = max(0, (curr_ndirs - prev['ndirs']) / dt)
                else:
                    rate_sofar = 0
                    rate_nfiles = 0
                    rate_ndirs = 0
                # Track max observed rates
                max_rates.setdefault(key, {'sofar': 0, 'nfiles': 0, 'ndirs': 0})
                max_rates[key]['sofar'] = max(max_rates[key]['sofar'], rate_sofar)
                max_rates[key]['nfiles'] = max(max_rates[key]['nfiles'], rate_nfiles)
                max_rates[key]['ndirs'] = max(max_rates[key]['ndirs'], rate_ndirs)
                # Save current as previous for next round
                prev_vals[key] = {
                    'sofar_bytes': curr_sofar,
                    'nfiles': curr_nfiles,
                    'ndirs': curr_ndirs,
                    'time': curr_time
                }
                updates.append({
                    'rate_sofar': rate_sofar,
                    'rate_nfiles': rate_nfiles,
                    'rate_ndirs': rate_ndirs,
                    'max_rate_sofar': max_rates[key]['sofar'],
                    'max_rate_nfiles': max_rates[key]['nfiles'],
                    'max_rate_ndirs': max_rates[key]['ndirs'],
                    'sofar_bytes': curr_sofar,
                    'nfiles': curr_nfiles,
                    'ndirs': curr_ndirs,
                    'total_bytes': level.get('total_bytes', 0),
                    'current_file': level.get('path', ''),
                    'current_ftype': level.get('ftype', ''),
                    'client_name': bs.get('client_name', ''),
                    'backup_type': bs.get('backup_type', ''),
                    'last_update': datetime.fromtimestamp(entry.get('nowtm')).strftime('%Y-%m-%d %H:%M:%S')
                })
        socketio.emit('job_update', {'updates': updates})
        time.sleep(0.2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    job_id = request.json.get('job_id')
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400
    # Stop any previous simulation for this jobid
    if job_id in simulation_threads:
        simulation_threads[job_id].do_run = False
    # Start a new simulation thread
    def run_sim():
        t = threading.currentThread()
        simulate_job(job_id)
    thread = threading.Thread(target=run_sim)
    thread.daemon = True
    simulation_threads[job_id] = thread
    thread.start()
    return jsonify({'status': 'Simulation started'})

if __name__ == '__main__':
    socketio.run(app, debug=True) 