import re
import os
import hashlib
from datetime import datetime
from .models import LogEntry, db

combined_pattern = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<date>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\S+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
)

def parse_line(line):
    line = line.strip()
    if not line:
        return None
    m = combined_pattern.match(line)
    if not m:
        return None
    groups = m.groupdict()
    date_str = groups['date']
    try:
        dt = datetime.strptime(date_str, '%d/%b/%Y:%H:%M:%S %z')
    except ValueError:
        return None
    size = groups['size']
    if size == '-':
        size = 0
    else:
        size = int(size)
    status = int(groups['status'])
    line_hash = hashlib.sha256(line.encode()).hexdigest()
    return {
        'ip': groups['ip'],
        'date': dt,
        'method': groups['method'],
        'url': groups['url'],
        'protocol': groups['protocol'],
        'status': status,
        'size': size,
        'referer': groups['referer'] if groups['referer'] != '-' else '',
        'user_agent': groups['user_agent'] if groups['user_agent'] != '-' else '',
        'line_hash': line_hash
    }

def parse_files(log_dir, log_mask, db_session):
    import glob
    files = glob.glob(os.path.join(log_dir, log_mask))
    total_entries = 0
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parsed = parse_line(line)
                if not parsed:
                    continue
                existing = db_session.query(LogEntry).filter_by(line_hash=parsed['line_hash']).first()
                if existing:
                    continue
                entry = LogEntry(**parsed)
                db_session.add(entry)
                total_entries += 1
                if total_entries % 1000 == 0:
                    db_session.commit()
        db_session.commit()
    return total_entries
