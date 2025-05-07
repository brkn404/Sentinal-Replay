import json
import csv
from datetime import datetime

# Input data: paste your JSON lines into a file (one JSON object per line)
input_file = 'parselogs.lipsgcxap02.jobprog.log.out'
output_file = 'jobprog.csv'

with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow([
        'Job ID', 'Timestamp', 'Date', 'Client Name', 'Backup Type',
        'Num Files', 'Num Dirs',
        'Backupset sofar_bytes (GB)',
        'Regular File Path', 'Regular total_bytes (GB)', 'Regular sofar_bytes (GB)'
    ])

    for line in infile:
        try:
            data = json.loads(line)
            jobid = data['jobid']
            ts = data['bsProgs'][0]['update_tm']
            date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            client = data['bsProgs'][0]['client_name']
            btype = data['bsProgs'][0]['backup_type']
            nfiles = data['bsProgs'][0]['nfiles']
            ndirs = data['bsProgs'][0]['ndirs']
            
            backupset_sofar = None
            reg_path = None
            reg_total = None
            reg_sofar = None

            for level in data['bsProgs'][0]['levels']:
                if level['ftype'] == 'Backupset':
                    backupset_sofar = level.get('sofar_bytes', 0) / (1024 ** 3)  # to GB
                elif level['ftype'] == 'Regular':
                    reg_path = level.get('path', '')
                    reg_total = level.get('total_bytes', 0) / (1024 ** 3)
                    reg_sofar = level.get('sofar_bytes', 0) / (1024 ** 3)

            writer.writerow([
                jobid, ts, date_str, client, btype, nfiles, ndirs,
                f"{backupset_sofar:.2f}" if backupset_sofar is not None else '',
                reg_path,
                f"{reg_total:.2f}" if reg_total is not None else '',
                f"{reg_sofar:.2f}" if reg_sofar is not None else ''
            ])
        except Exception as e:
            print(f"Error processing line: {e}")
