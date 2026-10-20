from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response
from pathlib import Path
from datetime import datetime
import sqlite3, os, uuid, random, csv, io
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'static' / 'uploads'
DB_PATH = BASE_DIR / 'roadwatch.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)
app.secret_key = os.environ.get('ROADWATCH_SECRET', 'roadwatch-dev-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            image TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            damage_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )''')
        # Start with an empty database. Analytics are based on real user-submitted reports.


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_damage(image_path):
    """Safe demo detector. Replace with trained pothole YOLO weights for real AI predictions."""
    # Optional YOLO integration: requires ultralytics + compatible trained weights in models/pothole.pt.
    weights = BASE_DIR / 'models' / 'pothole.pt'
    if weights.exists():
        try:
            from ultralytics import YOLO
            model = YOLO(str(weights))
            result = model(str(image_path), verbose=False)[0]
            if len(result.boxes) > 0:
                confs = result.boxes.conf.tolist()
                confidence = max(confs) if confs else 0.75
                return 'Pothole', round(float(confidence), 2), 'High' if confidence >= .8 else 'Medium', len(result.boxes), 'YOLO model'
            return 'No damage detected', 0.0, 'Low', 0, 'YOLO model'
        except Exception:
            pass
    # Do not invent AI predictions when no trained model is configured.
    # The report is stored for human review and confidence is explicitly zero/unknown.
    return 'Manual review required', 0.0, 'Medium', 0, 'AI model not configured — manual review'


@app.route('/')
def index():
    with db() as con:
        reports = con.execute('SELECT * FROM reports ORDER BY id DESC LIMIT 6').fetchall()
        total = con.execute('SELECT COUNT(*) FROM reports').fetchone()[0]
        pending = con.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'").fetchone()[0]
        progress = con.execute("SELECT COUNT(*) FROM reports WHERE status='In Progress'").fetchone()[0]
        resolved = con.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'").fetchone()[0]
        high = con.execute("SELECT COUNT(*) FROM reports WHERE severity='High' AND status!='Resolved'").fetchone()[0]
    return render_template('index.html', reports=reports, total=total, pending=pending, progress=progress, resolved=resolved, high=high)


@app.route('/report', methods=['GET', 'POST'])
def report_damage():
    if request.method == 'POST':
        title = request.form.get('title', '').strip() or 'Road damage report'
        description = request.form.get('description', '').strip()
        lat_raw, lon_raw = request.form.get('latitude', '').strip(), request.form.get('longitude', '').strip()
        try:
            lat = float(lat_raw) if lat_raw else None
            lon = float(lon_raw) if lon_raw else None
            if lat is not None and not -90 <= lat <= 90: raise ValueError()
            if lon is not None and not -180 <= lon <= 180: raise ValueError()
        except ValueError:
            flash('Please enter valid GPS coordinates.', 'error')
            return redirect(url_for('report_damage'))
        file = request.files.get('image')
        if not file or not file.filename:
            flash('Please choose a road image to upload.', 'error')
            return redirect(url_for('report_damage'))
        if not allowed_file(file.filename):
            flash('Image must be PNG, JPG, JPEG, or WEBP.', 'error')
            return redirect(url_for('report_damage'))
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = UPLOAD_DIR / filename
        file.save(filepath)
        damage_type, confidence, severity, count, mode = detect_damage(filepath)
        with db() as con:
            con.execute('''INSERT INTO reports(title,description,image,latitude,longitude,damage_type,severity,confidence,status,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)''', (title, description, filename, lat, lon, damage_type, severity, confidence, 'Pending', datetime.now().strftime('%Y-%m-%d %H:%M')))
            report_id = con.execute('SELECT last_insert_rowid()').fetchone()[0]
        flash(f'Report #{report_id} submitted. Detection mode: {mode}.', 'success')
        return redirect(url_for('report_detail', report_id=report_id))
    return render_template('report.html')


@app.route('/reports')
def reports():
    status = request.args.get('status', '').strip()
    severity = request.args.get('severity', '').strip()
    q = request.args.get('q', '').strip()
    clauses, params = [], []
    if status in {'Pending', 'In Progress', 'Resolved'}:
        clauses.append('status=?'); params.append(status)
    if severity in {'Low', 'Medium', 'High', 'Critical'}:
        clauses.append('severity=?'); params.append(severity)
    if q:
        clauses.append('(title LIKE ? OR description LIKE ? OR damage_type LIKE ?)')
        params.extend([f'%{q}%'] * 3)
    sql = 'SELECT * FROM reports' + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ' ORDER BY id DESC'
    with db() as con:
        items = con.execute(sql, params).fetchall()
        total_matching = len(items)
    return render_template('reports.html', reports=items, selected_status=status, selected_severity=severity, search_query=q, total_matching=total_matching)


@app.route('/analytics')
def analytics():
    with db() as con:
        all_rows = con.execute('SELECT * FROM reports ORDER BY id').fetchall()
        by_status = con.execute('SELECT status, COUNT(*) AS count FROM reports GROUP BY status').fetchall()
        by_severity = con.execute('SELECT severity, COUNT(*) AS count FROM reports GROUP BY severity').fetchall()
        by_type = con.execute('SELECT damage_type, COUNT(*) AS count FROM reports GROUP BY damage_type ORDER BY count DESC').fetchall()
        by_month = con.execute("SELECT substr(created_at,1,7) AS month, COUNT(*) AS count FROM reports GROUP BY month ORDER BY month").fetchall()
        resolved = con.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'").fetchone()[0]
        total = len(all_rows)
        high_open = con.execute("SELECT COUNT(*) FROM reports WHERE severity IN ('High','Critical') AND status!='Resolved'").fetchone()[0]
    payload = {
        'status_labels': [r['status'] for r in by_status], 'status_values': [r['count'] for r in by_status],
        'severity_labels': [r['severity'] for r in by_severity], 'severity_values': [r['count'] for r in by_severity],
        'type_labels': [r['damage_type'] for r in by_type], 'type_values': [r['count'] for r in by_type],
        'month_labels': [r['month'] for r in by_month], 'month_values': [r['count'] for r in by_month]
    }
    resolution_rate = round((resolved / total) * 100) if total else 0
    return render_template('analytics.html', charts=payload, total=total, resolved=resolved, high_open=high_open, resolution_rate=resolution_rate, rows=all_rows)


@app.route('/export.csv')
def export_csv():
    status = request.args.get('status', '').strip()
    severity = request.args.get('severity', '').strip()
    q = request.args.get('q', '').strip()
    clauses, params = [], []
    if status in {'Pending', 'In Progress', 'Resolved'}:
        clauses.append('status=?'); params.append(status)
    if severity in {'Low', 'Medium', 'High', 'Critical'}:
        clauses.append('severity=?'); params.append(severity)
    if q:
        clauses.append('(title LIKE ? OR description LIKE ? OR damage_type LIKE ?)'); params.extend([f'%{q}%'] * 3)
    sql = 'SELECT id,title,description,damage_type,severity,confidence,status,latitude,longitude,created_at FROM reports' + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ' ORDER BY id DESC'
    with db() as con:
        rows = con.execute(sql, params).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Report ID','Title','Description','Damage Type','Severity','Confidence','Status','Latitude','Longitude','Created At'])
    for r in rows:
        writer.writerow([r['id'],r['title'],r['description'],r['damage_type'],r['severity'],r['confidence'],r['status'],r['latitude'],r['longitude'],r['created_at']])
    return Response('﻿' + output.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition':'attachment; filename=roadwatch_reports.csv'})


@app.route('/reports/<int:report_id>')
def report_detail(report_id):
    with db() as con:
        item = con.execute('SELECT * FROM reports WHERE id=?', (report_id,)).fetchone()
    if not item:
        flash('Report not found.', 'error')
        return redirect(url_for('reports'))
    return render_template('detail.html', report=item)


@app.route('/reports/<int:report_id>/status', methods=['POST'])
def update_status(report_id):
    status = request.form.get('status', '')
    if status not in {'Pending', 'In Progress', 'Resolved'}:
        flash('Invalid status.', 'error')
        return redirect(url_for('report_detail', report_id=report_id))
    with db() as con:
        con.execute('UPDATE reports SET status=? WHERE id=?', (status, report_id))
    flash('Repair status updated.', 'success')
    return redirect(url_for('report_detail', report_id=report_id))


@app.route('/map')
def damage_map():
    with db() as con:
        items = con.execute('SELECT * FROM reports WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY id DESC').fetchall()
    points = [dict(id=r['id'], title=r['title'], lat=r['latitude'], lon=r['longitude'], severity=r['severity'], status=r['status'], damage_type=r['damage_type']) for r in items]
    return render_template('map.html', points=points)


@app.route('/api/reports')
def api_reports():
    with db() as con:
        items = con.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in items])


@app.errorhandler(413)
def too_large(_error):
    flash('Image is too large. Maximum upload size is 8 MB.', 'error')
    return redirect(url_for('report_damage'))


init_db()
if __name__ == '__main__':
    print('\nRoadWatch AI is starting...')
    print('Open http://127.0.0.1:5000 in your browser.\n')
    app.run(debug=True)
