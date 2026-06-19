import threading
import uuid
import os
from .log_parser import parse_files
from .config import load_config
from . import db
from flask import current_app

tasks = {}

def start_parse_task():
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'status': 'running',
        'progress': 0,
        'total': 0,
        'processed': 0,
        'message': 'Starting...'
    }
    thread = threading.Thread(target=run_parse, args=(task_id,))
    thread.daemon = True
    thread.start()
    return task_id

def run_parse(task_id):
    config = load_config()
    log_dir = config['LOG_DIR']
    log_mask = config['LOG_MASK']
    from .models import LogEntry
    with current_app.app_context():
        import glob
        files = glob.glob(os.path.join(log_dir, log_mask))
        tasks[task_id]['total'] = len(files)
        processed = 0
        total_entries = 0
        for i, filepath in enumerate(files):
            entries = parse_files_single(filepath, db.session)
            total_entries += entries
            processed += 1
            tasks[task_id]['progress'] = int((processed / len(files)) * 100)
            tasks[task_id]['processed'] = processed
            tasks[task_id]['message'] = f'Parsed {processed} of {len(files)} files, {total_entries} entries'
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['message'] = f'Done, parsed {total_entries} entries'
        tasks[task_id]['progress'] = 100

def parse_files_single(filepath, session):
    from .log_parser import parse_line
    from .models import LogEntry
    count = 0
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_line(line)
            if not parsed:
                continue
            existing = session.query(LogEntry).filter_by(line_hash=parsed['line_hash']).first()
            if existing:
                continue
            entry = LogEntry(**parsed)
            session.add(entry)
            count += 1
            if count % 1000 == 0:
                session.commit()
    session.commit()
    return count

def get_task_status(task_id):
    return tasks.get(task_id)

def get_parsed_files():
    return ['access.log.1', 'access.log.2', 'access.log']
