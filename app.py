import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time, sys
from urllib.parse import quote

# --- FFmpeg Configuration ---
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

app = Flask(__name__)
tasks = {}

# --- Cleanup Loop ---
def cleanup_loop():
    while True:
        try:
            current_time = time.time()
            to_delete = []
            for uid, task in list(tasks.items()):
                if current_time - task.get('timestamp', 0) > 1200:
                    fpath = task.get('file')
                    if fpath and os.path.exists(fpath):
                        try: os.remove(fpath)
                        except: pass
                    for f in os.listdir('.'):
                        if f.startswith(uid):
                            try: os.remove(f)
                            except: pass
                    to_delete.append(uid)
            for uid in to_delete:
                del tasks[uid]
        except: pass
        time.sleep(60)

threading.Thread(target=cleanup_loop, daemon=True).start()

# --- HTML (זהה לעיצוב הרטרו שאהבת) ---
HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>NOKIA SYSTEM V.1.0</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=VT323&display=swap" rel="stylesheet">
<style>
:root { --green: #33ff00; --dim: #003300; --bg: #050505; }
body { margin:0; min-height:100vh; background-color: var(--bg); 
       font-family: 'VT323', monospace; color: var(--green);
       display: flex; justify-content: center; align-items: center; 
       overflow-x: hidden; text-transform: uppercase; letter-spacing: 1px;}
body::before { content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
    z-index: 2; background-size: 100% 2px, 3px 100%; pointer-events: none; }
.scanline { width: 100%; height: 100px; z-index: 10; background: linear-gradient(0deg, rgba(0,0,0,0) 0%, rgba(33, 255, 0, 0.04) 50%, rgba(0,0,0,0) 100%); opacity: 0.1; position: absolute; bottom: 100%; animation: scanline 10s linear infinite; pointer-events: none; }
@keyframes scanline { 0% {bottom:100%;} 80% {bottom:100%;} 100% {bottom:-100%;} }
.terminal { width: 90%; max-width: 420px; border: 2px solid var(--green); padding: 20px; position: relative; box-shadow: 0 0 20px var(--dim), inset 0 0 20px var(--dim); z-index: 3; background: rgba(0, 10, 0, 0.9); }
h2 { margin: 0 0 15px 0; font-size: 32px; text-shadow: 0 0 5px var(--green); border-bottom: 2px dashed var(--dim); padding-bottom:10px; text-align: center;}
label { display: block; margin-top: 15px; font-size: 20px;}
input, select, button { width: 100%; background: #000; border: 1px solid var(--green); color: var(--green); padding: 10px; font-family: 'VT323', monospace; font-size: 20px; margin-top: 5px; box-sizing: border-box; outline: none;}
input:focus, select:focus { background: var(--dim); box-shadow: 0 0 8px var(--green); }
button { margin-top: 20px; background: var(--green); color: #000; font-weight: bold; cursor: pointer; border:none;}
button:hover { background: #fff; box-shadow: 0 0 15px var(--green); }
button:disabled { background: var(--dim); color: var(--green); cursor: wait; }
.checkbox-wrapper { display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--dim); padding: 8px; margin-top: 10px; }
input[type="checkbox"] { width: auto; transform: scale(1.5); accent-color: var(--green); cursor: pointer;}
.output { margin-top: 20px; border-top: 2px dashed var(--dim); padding-top: 10px; display: none;}
.prog-container { width: 100%; border: 1px solid var(--green); height: 20px; padding: 2px; margin: 10px 0; box-sizing: border-box;}
.prog-bar { height: 100%; background: repeating-linear-gradient(90deg, var(--green) 0px, var(--green) 10px, #000 10px, #000 12px); width: 0%; transition: width 0.2s; }
.log { font-size: 18px; margin-top: 5px; min-height: 1.2em;}
.blink { animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }
img { width: 100px; border: 1px solid var(--green); display:none; margin: 0 auto; display: block; filter: grayscale(100%) contrast(1.2) sepia(100%) hue-rotate(90deg); }
.header-dec { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 16px; color: var(--dim);}
</style>
</head>
<body>
<div class="scanline"></div>
<div class="terminal">
    <div class="header-dec"><span>SYS.ROOT</span><span>ONLINE</span></div>
    <h2>&lt;NOKIA_CLOUD /&gt;</h2>
    <label>&gt; TARGET_URL:</label>
    <input id="url" placeholder="ENTER LINK HERE...">
    <label>&gt; OUTPUT_FORMAT:</label>
    <select id="mode">
        <option value="360">VIDEO [MP4/NORMAL]</option>
        <option value="mp3">AUDIO [MP3/MUSIC]</option>
    </select>
    <div class="checkbox-wrapper">
        <label for="nokiaSwitch" style="margin:0; cursor:pointer;">&gt; RETRO_MODE [AVI/240p]</label>
        <input type="checkbox" id="nokiaSwitch" checked>
    </div>
    <button onclick="execute()" id="btn">[ INITIALIZE ]</button>
    <div id="outputArea" class="output">
        <img id="thumb">
        <div class="log" style="text-align:center; margin-bottom:5px;" id="videoTitle"></div>
        <div class="prog-container"><div class="prog-bar" id="bar"></div></div>
        <div class="log">STATUS: <span id="status">WAITING</span><span class="blink">_</span></div>
    </div>
</div>
<script>
let id=null, pollInterval=null;
function execute() {
    const url = document.getElementById('url').value;
    const mode = document.getElementById('mode').value;
    const nokia = document.getElementById('nokiaSwitch').checked;
    if (!url) return;
    document.getElementById('btn').disabled = true;
    document.getElementById('btn').innerText = "[ PROCESSING... ]";
    document.getElementById('outputArea').style.display = 'block';
    document.getElementById('thumb').style.display = 'none';
    document.getElementById('videoTitle').innerText = '';
    document.getElementById('bar').style.width = '0%';
    document.getElementById('status').innerText = "CONNECTING...";
    fetch('/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url, mode: mode, nokia: nokia })
    }).then(r => r.json()).then(d => {
        if(d.error) throw d.error;
        id = d.id;
        pollInterval = setInterval(checkStatus, 1000);
    }).catch(e => {
        document.getElementById('status').innerText = "ERR: " + e;
        document.getElementById('btn').disabled = false;
        document.getElementById('btn').innerText = "[ RETRY ]";
    });
}
function checkStatus() {
    fetch('/progress/' + id).then(r => r.json()).then(d => {
        if (d.error) {
            clearInterval(pollInterval);
            document.getElementById('status').innerText = "SYSTEM HALTED: " + d.error;
            document.getElementById('btn').disabled = false;
            document.getElementById('btn').innerText = "[ RETRY ]";
            return;
        }
        document.getElementById('bar').style.width = d.percent + '%';
        if (d.thumb && document.getElementById('thumb').style.display === 'none') {
            document.getElementById('thumb').src = d.thumb;
            document.getElementById('thumb').style.display = 'block';
        }
        if (d.title) document.getElementById('videoTitle').innerText = d.title.substring(0,30);
        
        let status = "DOWNLOADING... " + d.percent + "%";
        if (d.converting) status = "ENCODING >> " + (d.mode === 'nokia' ? 'AVI' : 'MP4');
        if (d.done) status = "COMPLETED.";
        document.getElementById('status').innerText = status;

        if (d.done) {
            clearInterval(pollInterval);
            document.getElementById('btn').disabled = false;
            document.getElementById('btn').innerText = "[ DOWNLOAD FILE ]";
            document.getElementById('btn').onclick = function() { window.location.href = '/file/' + id; };
            window.location.href = '/file/' + id;
        }
    });
}
</script>
</body>
</html>
"""

def processing_thread(uid, url, mode_val, is_nokia):
    try:
        tasks[uid]['timestamp'] = time.time()
        
        # ---------------------------------------------------------
        # התיקון הקריטי ל-Youtube: התחזות לאנדרואיד
        # זה עוקף את חסימות הבוטים של גוגל
        # ---------------------------------------------------------
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            # פורמט חכם יותר: מנסה למצוא MP4 ישיר, אם לא, ממזג וידאו ואודיו
            'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]/best',
            'nocheckcertificate': True,
            # ה-Arg הזה קריטי בשרתים (טוען שאנחנו אפליקציית מובייל)
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'],
                }
            }
        }

        # התעלמות מקוקיז בכוונה - הן גורמות לבעיות אם הן לא מה-IP של השרת
        # if os.path.exists('cookies.txt'): ... (הוסר כדי למנוע חסימות)

        if mode_val == 'mp3' and not is_nokia:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]

        def hook(d):
            if d['status'] == 'downloading':
                try: 
                    p = d.get('_percent_str', '0%').replace('%','')
                    tasks[uid]['percent'] = int(float(p))
                except: pass
            if d['status'] == 'finished':
                tasks[uid]['percent'] = 98
                tasks[uid]['converting'] = True

        ydl_opts['progress_hooks'] = [hook]

        dl_filename = None
        info = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. ניסיון הורדה
            info = ydl.extract_info(url, download=True)
            tasks[uid]['title'] = info.get('title', 'Unknown')
            tasks[uid]['thumb'] = info.get('thumbnail')
            
            # 2. זיהוי שם הקובץ שירד
            # ייתכן שזה יהיה mkv אם התבצע מיזוג, או mp4/webm
            base = ydl.prepare_filename(info)
            # בודקים אם הקובץ קיים בדיוק בשם ש-ydl חשב
            if os.path.exists(base):
                dl_filename = base
            else:
                # אם לא, מחפשים לפי ה-UID
                for f in os.listdir('.'):
                    if f.startswith(f"{uid}_src"):
                        dl_filename = f
                        break
        
        if not dl_filename or not os.path.exists(dl_filename):
            raise Exception("Download Error: File not created")

        # עיבוד סופי
        safe_title = "".join([c for c in info.get('title','video') if c.isalnum() or c in ' .-_']).strip()
        
        if is_nokia and mode_val != 'mp3':
            # === NOKIA MODE: AVI ===
            tasks[uid]['mode'] = 'nokia'
            final_name = f"{uid}_nokia.avi"
            display_name = f"{safe_title}.avi"
            
            cmd = [
                'ffmpeg', '-y', '-i', dl_filename,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20', 
                '-c:v', 'mpeg4', '-vtag', 'xvid', '-q:v', '10', # q:v נותן דחיסה מאוזנת
                '-c:a', 'libmp3lame', '-ac', '1', '-ar', '22050', '-b:a', '64k',
                final_name
            ]
            subprocess.run(cmd, check=True)
            try: os.remove(dl_filename)
            except: pass
            
        elif mode_val == 'mp3':
             # אודיו
             ext = dl_filename.split('.')[-1]
             final_name = f"{uid}_audio.{ext}"
             display_name = f"{safe_title}.{ext}"
             os.rename(dl_filename, final_name)
        
        else:
             # רגיל (MP4) - המרה בטוחה למקרה שהגיע פורמט MKV/WebM
             final_name = f"{uid}_vid.mp4"
             display_name = f"{safe_title}.mp4"
             # המרה מהירה ל-MP4
             cmd = ['ffmpeg', '-y', '-i', dl_filename, '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', final_name]
             subprocess.run(cmd, check=True)
             try: os.remove(dl_filename)
             except: pass

        tasks[uid]['file'] = final_name
        tasks[uid]['display_name'] = display_name
        tasks[uid]['percent'] = 100
        tasks[uid]['done'] = True
        
    except Exception as e:
        print(f"Error for {uid}: {e}")
        tasks[uid]['error'] = str(e)
        try:
            for f in os.listdir('.'):
                 if f.startswith(uid): os.remove(f)
        except: pass

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    uid = str(uuid.uuid4())
    is_nokia = data.get('nokia', False)
    mode = data.get('mode', '360')
    
    tasks[uid] = {
        'percent': 0, 
        'done': False, 
        'mode': mode,
        'converting': False,
        'timestamp': time.time()
    }
    
    threading.Thread(target=processing_thread, args=(uid, data['url'], mode, is_nokia)).start()
    return jsonify({'id': uid})

@app.route('/progress/<id>')
def prog(id):
    return jsonify(tasks.get(id, {'error': 'ID_NOT_FOUND'}))

@app.route('/file/<id>')
def get_file(id):
    task = tasks.get(id)
    if not task: return "FILE_DELETED", 404
    fpath = task.get('file')
    if not fpath or not os.path.exists(fpath): return "ERROR_MISSING_FILE", 404

    dname = task.get('display_name', 'video')
    try: encoded = quote(dname)
    except: encoded = "download"
    
    def generate():
        with open(fpath, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk: break
                yield chunk
    
    res = Response(generate(), mimety
