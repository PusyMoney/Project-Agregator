from flask import Blueprint, request, jsonify, session
from sqlalchemy import func, and_, or_
from datetime import datetime
from .models import LogEntry, db
from .tasks import start_parse_task, get_task_status, get_parsed_files

api_bp = Blueprint('api', __name__)

def get_user_id_from_token():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return None
    token = token[7:]
    return session.get(token)

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    ip = request.args.get('ip')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    keyword = request.args.get('keyword')
    url_filter = request.args.get('url')
    group_by = request.args.get('group_by')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    query = LogEntry.query

    if ip:
        query = query.filter(LogEntry.ip == ip)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(LogEntry.date >= dt_from)
        except:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.filter(LogEntry.date <= dt_to)
        except:
            pass
    if keyword:
        query = query.filter(or_(
            LogEntry.url.contains(keyword),
            LogEntry.user_agent.contains(keyword)
        ))
    if url_filter:
        query = query.filter(LogEntry.url == url_filter)

    if group_by:
        if group_by == 'ip':
            result = query.with_entities(
                LogEntry.ip,
                func.count().label('count'),
                func.min(LogEntry.date).label('first'),
                func.max(LogEntry.date).label('last')
            ).group_by(LogEntry.ip).order_by(func.count().desc())
            items = []
            for row in result:
                items.append({
                    'group': row.ip,
                    'count': row.count,
                    'first': row.first.isoformat() if row.first else None,
                    'last': row.last.isoformat() if row.last else None
                })
            return jsonify({'data': items, 'total': len(items)}), 200
        elif group_by == 'url':
            result = query.with_entities(
                LogEntry.url,
                func.count().label('count')
            ).group_by(LogEntry.url).order_by(func.count().desc())
            items = [{'url': row.url, 'count': row.count} for row in result]
            return jsonify({'data': items, 'total': len(items)}), 200
        elif group_by == 'date':
            result = query.with_entities(
                func.date(LogEntry.date).label('day'),
                func.count().label('count')
            ).group_by('day').order_by('day')
            items = [{'date': str(row.day), 'count': row.count} for row in result]
            return jsonify({'data': items, 'total': len(items)}), 200

    total = query.count()
    logs = query.order_by(LogEntry.date.desc()).limit(limit).offset(offset).all()
    return jsonify({
        'data': [log.to_dict() for log in logs],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    total = LogEntry.query.count()
    unique_ips = db.session.query(func.count(func.distinct(LogEntry.ip))).scalar()
    urls_count = db.session.query(func.count(func.distinct(LogEntry.url))).scalar()
    return jsonify({
        'total_entries': total,
        'unique_ips': unique_ips,
        'unique_urls': urls_count
    }), 200

@api_bp.route('/urls', methods=['GET'])
def get_urls():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    result = db.session.query(
        LogEntry.url,
        func.count().label('count')
    ).group_by(LogEntry.url).order_by(func.count().desc()).all()
    data = [{'url': row.url, 'count': row.count} for row in result]
    return jsonify({'data': data}), 200

@api_bp.route('/parse', methods=['POST'])
def start_parse():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    task_id = start_parse_task()
    return jsonify({'task_id': task_id}), 202

@api_bp.route('/parse/status/<task_id>', methods=['GET'])
def parse_status(task_id):
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    status = get_task_status(task_id)
    if status is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(status), 200

@api_bp.route('/parse/files', methods=['GET'])
def parse_files_list():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    files = get_parsed_files()
    return jsonify({'files': files}), 200
