import os, threading, uuid, time, subprocess, yt_dlp
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
tasks = {}

# הגדרות שרת
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # הגבלה ל-100MB

# הגדרות FFmpeg
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

RES_OPTIONS = {
    "144p": "176:144",
    "240p": "320:240", # אידיאלי לנוקיה
    "360p": "480:360",
    "480p": "640:480"
}

# --- דף הבית (ממשק האתר) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Nokia Factory Cloud</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; text-align: center; padding: 20px; margin: 0; }
        .window { max-width: 550px; margin: auto; border: 2px solid #00ff41; padding: 25px; box-shadow: 0 0 20px #003b00; background: rgba(0,10,0,0.95); position: relative; }
        
        /* טאבים */
        .tabs { display: flex; margin-bottom: 20px; border-bottom: 2px solid #00ff41; }
        .tab { flex: 1; padding: 12px; cursor: pointer; background: #001a00; border: 1px solid #00ff41; border-bottom: none; }
        .tab.active { background: #00ff41; color: #000; font-weight: bold; }
        
        .content-section { display: none; padding: 15px 0; }
        .content-section.active { display: block; }

        input, select, button { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #00ff41; color: #fff; font-family: inherit; font-size: 15px; border-radius: 4px; box-sizing: border-box; }
        button { background: #00ff41; color: #000; font-weight: bold; cursor: pointer; transition: 0.2s; border: none; margin-top: 20px; }
        button:hover { background: #fff; }
        button:disabled { background: #333; color: #777; cursor: not-allowed; }
        
        .status-box { margin-top: 20px; background: #050505; border: 1px dashed #00ff41; padding: 12px; font-size: 13px; min-height: 40px; color: cyan; }
        .badge { font-size: 10px; background: #00ff41; color: #000; padding: 1px 4px; vertical-align: middle; margin-right: 5px; }
    </style>
</head>
<body>
    <div class="window">
        <header>
            <h1 style="margin-top:0;">SYSTEM_FACTORY v5.0</h1>
            <p style="font-size:12px; color: #008800;">CLOD_ENCODER // SECURE_CONVERSION</p>
        </header>

        <div class="tabs">
            <div class="tab active" id="tab-url" onclick="showTab('url')">הורדה מהרשת</div>
            <div class="tab" id="tab-file" onclick="showTab('file')">העלאת קובץ</div>
        </div>

        <!-- אזור 1: הורדה מהרשת -->
        <div id="section-url" class="content-section active">
            <input type="text" id="url-input" placeholder=">> הדבק לינק (YT / TikTok / FB)...">
        </div>

        <!-- אזור 2: העלאת קובץ -->
        <div id="section-file" class="content-section">
            <input type="file" id="file-input">
            <p style="font-size: 10px; color: #888;">מקסימום גודל: 100MB</p>
        </div>

        <!-- הגדרות משותפות -->
        <div style="text-align: right; border-top: 1px solid #003300; padding-top: 10px;">
            <label>פורמט פלט:</label>
            <select id="fmt-select">
                <option value="mp4">VIDEO - MP4 (הכי מומלץ)</option>
                <option value="avi">VIDEO - AVI (רטרו)</option>
                <option value="3gp">PHONE - 3GP (נוקיה ישן מאוד)</option>
                <option value="mp3">MUSIC - MP3 (אודיו בלבד)</option>
            </select>

            <label>רזולוציית נוקיה:</label>
            <select id="res-select">
                <option value="144p">144p (מסך קטן)</option>
                <option value="240p" selected>240p (אידיאלי - NOKIA RECO)</option>
                <option value="360p">360p (מסך רחב)</option>
                <option value="480p">480p (איכות מקסימלית)</option>
            </select>
        </div>

        <button onclick="ignite()" id="main-btn">בצע פקודה והורד קובץ</button>
        <div class="status-box" id="stat-log">WAITING_FOR_DATA_STREAM...</div>
    </div>

    <script>
        let currentTab = 'url';

        function showTab(type) {
            currentTab = type;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.getElementById('tab-' + type).classList.add('active');
            document.getElementById('section-' + type).classList.add('active');
        }

        function ignite() {
            const btn = document.getElementById('main-btn');
            const log = document.getElementById('stat-log');
            const fmt = document.getElementById('fmt-select').value;
            const res = document.getElementById('res-select').value;
            
            let formData = new FormData();
            formData.append('format', fmt);
            formData.append('res', res);
            formData.append('type', currentTab);

            if (currentTab === 'url') {
                const url = document.getElementById('url-input').value;
                if (!url) return alert("חסר קישור!");
                formData.append('url', url);
            } else {
                const file = document.getElementById('file-input').files[0];
                if (!file) return alert("בחר קובץ מהמכשיר!");
                formData.append('file', file);
            }

            btn.disabled = true;
            log.innerText = "INITIALIZING_SYSTEM... (Please Wait)";

            fetch('/api/process', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) throw data.error;
                const uid = data.id;
                monitor(uid);
            })
            .catch(err => {
                alert("ERR: " + err);
                resetUI();
            });
        }

        function monitor(uid) {
            const interval = setInterval(() => {
                fetch('/api/status/' + uid)
                .then(r => r.json())
                .then(s => {
                    document.getElementById('stat-log').innerText = "PROGRESS: " + s.status;
                    if (s.status === "DONE") {
                        clearInterval(interval);
                        document.getElementById('stat-log').innerText = "DONE! DATA PACKED. STARTING_DOWNLOAD...";
                        window.location.href = '/api/get/' + uid;
                        setTimeout(resetUI, 3000);
                    } else if (s.status.includes("ERROR")) {
                        clearInterval(interval);
                        alert(s.status);
                        resetUI();
                    }
                });
            }, 2000);
        }

        function resetUI() {
            document.getElementById('main-btn').disabled = false;
            document.getElementById('main-btn').innerText = "בצע פקודה והורד קובץ";
        }
    </script>
</body>
</html>
"""

# --- פונקציית המנוע (עובדת בשני המצבים) ---
def encoder_worker(uid, source_path, is_yt, format_ext, resolution):
    try:
        final_file = f"{uid}_final.{format_ext}"
        
        # 1. שלב ההורדה (אם זה קישור)
        if is_yt:
            tasks[uid]['status'] = "DOWNLOADING_REMOTE_SOURCE..."
            ydl_opts = {'outtmpl': source_path, 'format': 'best', 'nocheckcertificate': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([source_path])
        
        # 2. שלב ההמרה (לכולם)
        tasks[uid]['status'] = f"RECODING_FOR_NOKIA ({resolution})..."
        scale = RES_OPTIONS.get(resolution, "320:240")
        
        if format_ext == "mp3":
            cmd = ['ffmpeg', '-y', '-i', source_path, '-vn', '-ab', '128k', final_file]
        else:
            cmd = ['ffmpeg', '-y', '-i', source_path, 
                   '-vf', f'scale={scale}:force_original_aspect_ratio=decrease,pad={scale.split(":")[0]}:{scale.split(":")[1]}:(ow-iw)/2:(oh-ih)/2']
            if format_ext == "mp4":
                cmd += ['-c:v', 'libx264', '-profile:v', 'baseline', '-c:a', 'aac', '-b:a', '64k', final_file]
            elif format_ext == "avi":
                cmd += ['-c:v', 'mpeg4', '-vtag', 'xvid', '-q:v', '8', '-c:a', 'libmp3lame', final_file]
            elif format_ext == "3gp":
                cmd += ['-s', '176x144', '-r', '15', '-b:v', '100k', '-ac', '1', '-ar', '8000', final_file]

        subprocess.run(cmd, check=True)
        
        # סיום
        tasks[uid]['file'] = final_file
        tasks[uid]['status'] = "DONE"
        
        # ניקוי המקור
        if os.path.exists(source_path):
            os.remove(source_path)
            
    except Exception as e:
        tasks[uid]['status'] = f"ERROR: {str(e)}"

# --- API ---

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/process', methods=['POST'])
def handle_request():
    uid = str(uuid.uuid4())
    req_type = request.form.get('type')
    fmt = request.form.get('format', 'mp4')
    res = request.form.get('res', '240p')
    
    tasks[uid] = {'status': 'QUEUED', 'timestamp': time.time()}

    if req_type == 'url':
        url = request.form.get('url')
        source_path = f"{uid}_src_tmp"
        threading.Thread(target=encoder_worker, args=(uid, url, True, fmt, res)).start()
    else:
        file = request.files.get('file')
        if not file: return jsonify({'error': 'No file uploaded'}), 400
        source_path = secure_filename(f"{uid}_{file.filename}")
        file.save(source_path)
        threading.Thread(target=encoder_worker, args=(uid, source_path, False, fmt, res)).start()

    return jsonify({'id': uid})

@app.route('/api/status/<uid>')
def get_status(uid):
    return jsonify(tasks.get(uid, {'status': 'NOT_FOUND'}))

@app.route('/api/get/<uid>')
def get_final(uid):
    task = tasks.get(uid)
    if task and task['status'] == 'DONE':
        return send_from_directory('.', task['file'], as_attachment=True)
    return "NOT_READY", 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
