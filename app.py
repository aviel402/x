import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time, sys
from urllib.parse import quote

# --- FFmpeg Path Check ---
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
                # Clean after 20 minutes
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

# --- עיצוב NEON CYBERPUNK ---
HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>NOKIA FLUX GENERATOR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
<style>
/* Base Setup */
:root {
    --primary: #00f3ff;
    --secondary: #bc13fe;
    --bg: #050510;
    --glass: rgba(255, 255, 255, 0.05);
}

body {
    margin: 0; min-height: 100vh;
    background-color: var(--bg);
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(188, 19, 254, 0.1), transparent 25%), 
        radial-gradient(circle at 85% 30%, rgba(0, 243, 255, 0.1), transparent 25%);
    font-family: 'Rajdhani', sans-serif;
    color: #fff;
    display: flex; justify-content: center; align-items: center;
    overflow-x: hidden;
}

/* Background Grid Animation */
body::before {
    content: ''; position: absolute;
    width: 200%; height: 200%;
    top: -50%; left: -50%;
    background-image: 
        linear-gradient(rgba(0, 243, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px);
    background-size: 40px 40px;
    transform: perspective(500px) rotateX(60deg);
    animation: gridMove 20s linear infinite;
    z-index: -1;
    pointer-events: none;
}

@keyframes gridMove {
    0% { transform: perspective(500px) rotateX(60deg) translateY(0); }
    100% { transform: perspective(500px) rotateX(60deg) translateY(40px); }
}

.container {
    width: 90%; max-width: 460px;
    background: var(--glass);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 15px;
    padding: 30px;
    box-shadow: 
        0 0 20px rgba(0, 243, 255, 0.2),
        inset 0 0 20px rgba(188, 19, 254, 0.1);
    position: relative;
}

/* Decor Corners */
.container::after {
    content: ''; position: absolute;
    top: -2px; left: -2px; right: -2px; bottom: -2px;
    background: linear-gradient(45deg, var(--primary), transparent, var(--secondary));
    z-index: -1;
    border-radius: 16px;
    filter: blur(5px);
    opacity: 0.6;
}

h1 {
    font-family: 'Orbitron', sans-serif;
    text-align: center;
    font-size: 28px;
    text-transform: uppercase;
    margin-bottom: 25px;
    letter-spacing: 3px;
    text-shadow: 0 0 10px var(--primary);
    background: linear-gradient(90deg, #fff, var(--primary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

label {
    display: block; margin-bottom: 8px; font-weight: 700; color: var(--primary);
    font-size: 14px; text-transform: uppercase; letter-spacing: 1px;
}

input, select {
    width: 100%;
    padding: 15px;
    background: rgba(0,0,0,0.4);
    border: 1px solid var(--primary);
    border-radius: 5px;
    color: #fff;
    font-family: 'Orbitron', monospace;
    font-size: 14px;
    box-sizing: border-box;
    transition: 0.3s;
    margin-bottom: 20px;
    outline: none;
}

input:focus, select:focus {
    box-shadow: 0 0 15px var(--primary);
    border-color: #fff;
}

/* Custom "Launch" Button */
button {
    width: 100%;
    padding: 15px;
    background: transparent;
    border: 2px solid var(--secondary);
    color: var(--secondary);
    font-family: 'Orbitron', sans-serif;
    font-size: 18px;
    font-weight: bold;
    text-transform: uppercase;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: 0.3s;
    box-shadow: 0 0 10px rgba(188, 19, 254, 0.3);
}

button:hover {
    background: var(--secondary);
    color: #000;
    box-shadow: 0 0 30px var(--secondary);
}

button:disabled {
    border-color: #555;
    color: #555;
    background: transparent;
    cursor: not-allowed;
    box-shadow: none;
}

/* Status & Progress */
.output-area {
    margin-top: 30px;
    border-top: 1px dashed rgba(255,255,255,0.2);
    padding-top: 20px;
    display: none;
}

.status-bar {
    display: flex; justify-content: space-between;
    margin-bottom: 5px;
    font-size: 14px;
    color: var(--primary);
    text-shadow: 0 0 5px var(--primary);
}

.progress-bg {
    height: 8px; background: rgba(255,255,255,0.1);
    border-radius: 4px; overflow: hidden;
}

.progress-fill {
    height: 100%; width: 0%;
    background: linear-gradient(90deg, var(--primary), var(--secondary));
    box-shadow: 0 0 10px var(--primary);
    transition: width 0.4s ease-out;
}

img#thumb {
    width: 100%; border: 1px solid var(--secondary);
    box-shadow: 0 0 15px rgba(188,19,254,0.3);
    margin-top: 20px; display: none;
    filter: sepia(20%) hue-rotate(180deg) saturate(200%); /* Cool effect */
}

#title-display {
    font-size: 12px; text-align: center; margin-top: 10px; color: #aaa;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
</style>
</head>
<body>

<div class="container">
    <h1>Flux Generator // <span style="font-size:0.6em">NOKIA 235</span></h1>
    
    <label>Target URL</label>
    <input type="text" id="url" placeholder="Paste Link Here...">

    <label>Operation Mode</label>
    <select id="mode">
        <option value="360">STANDARD [MP4 360p]</option>
        <option value="mp3">AUDIO EXTRACT [MP3]</option>
        <option value="nokia">NOKIA 235 OPTIMIZED [MP4 QVGA]</option>
    </select>

    <button onclick="ignite()" id="btn">INITIALIZE</button>

    <div class="output-area" id="output">
        <div class="status-bar">
            <span id="status">STANDBY</span>
            <span id="percent">0%</span>
        </div>
        <div class="progress-bg">
            <div class="progress-fill" id="bar"></div>
        </div>
        <img id="thumb">
        <div id="title-display"></div>
    </div>
</div>

<script>
let id = null;
let looper = null;

function ignite(){
    const url = document.getElementById('url').value;
    const mode = document.getElementById('mode').value;

    if(!url) return alert("NO TARGET DETECTED");

    // UI Trigger
    document.getElementById('btn').disabled = true;
    document.getElementById('btn').innerHTML = "PROCESSING &rsaquo;&rsaquo;&rsaquo;";
    document.getElementById('output').style.display = 'block';
    document.getElementById('thumb').style.display = 'none';
    document.getElementById('bar').style.width = '0%';
    document.getElementById('status').innerText = "CONNECTING...";
    
    fetch('/start', {
        method: 'POST', 
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({url:url, mode:mode})
    })
    .then(r => r.json())
    .then(d => {
        if(d.error) throw d.error;
        id = d.id;
        looper = setInterval(monitor, 1000);
    })
    .catch(e => {
        alert("SYSTEM FAIL: " + e);
        reset();
    });
}

function monitor(){
    if(!id) return;
    fetch('/progress/'+id).then(r=>r.json()).then(d=>{
        
        if(d.error) {
            clearInterval(looper);
            document.getElementById('status').innerText = "FAILURE";
            alert(d.error);
            reset();
            return;
        }

        // Stats
        document.getElementById('percent').innerText = d.percent + '%';
        document.getElementById('bar').style.width = d.percent + '%';
        
        if(d.title) document.getElementById('title-display').innerText = d.title;
        if(d.thumb && document.getElementById('thumb').style.display === 'none'){
            document.getElementById('thumb').src = d.thumb;
            document.getElementById('thumb').style.display = 'block';
        }

        let txt = "DOWNLOADING...";
        if(d.converting) txt = "COMPRESSING FLUX...";
        if(d.done) txt = "COMPLETE.";
        document.getElementById('status').innerText = txt;

        if(d.done){
            clearInterval(looper);
            window.location.href = '/file/'+id;
            document.getElementById('btn').innerHTML = "DOWNLOAD READY";
            setTimeout(reset, 2500);
        }

    }).catch(e => console.log(e));
}

function reset(){
    document.getElementById('btn').disabled = false;
    document.getElementById('btn').innerText = "INITIALIZE";
}
</script>
</body>
</html>
"""

def process_task(uid, url, mode):
    try:
        tasks[uid]['timestamp'] = time.time()
        
        # --- YouTube Download Config (עם קוקיז!) ---
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            'format': 'best[height<=360]/best',
            'nocheckcertificate': True,
            # שינוי משמעותי: לא עוד אנדרואיד, סומכים על הקוקיז של המשתמש
             'extractor_args': {
                'youtube': {
                    'player_client': ['android'], # עדיין משאיר ליתר ביטחון, עובד טוב בשילוב
                }
            }
        }

        # !!!!!!! החלק הקריטי !!!!!!!
        # בודק אם הקובץ קיים בשרת וטוען אותו
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        if mode == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

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

        info = None
        dl_file = None
        
        # שלב 1: הורדה
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            tasks[uid]['title'] = info.get('title', 'Video')
            tasks[uid]['thumb'] = info.get('thumbnail')
            
            # איתור קובץ
            base_guess = ydl.prepare_filename(info)
            if os.path.exists(base_guess): dl_file = base_guess
            else:
                for f in os.listdir('.'):
                    if f.startswith(f"{uid}_src"):
                        dl_file = f; break
        
        if not dl_file: raise Exception("File extraction failed")

        # שלב 2: עיבוד
        safe_title = "".join([c for c in info.get('title','v') if c.isalnum() or c in ' -_']).strip()
        final_file = ""

        # === מצב נוקיה 235 (2024 / S30+) ===
        # MP4 / H.264 Baseline / AAC
        # זה עדיף משמעותית על AVI במכשירים החדשים של נוקיה
        if mode == 'nokia':
            final_file = f"{uid}_nokia.mp4"
            safe_title += "_nokia.mp4"
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20',               # FPS מתון
                '-c:v', 'libx264',        # קודק מודרני יותר אך קל
                '-profile:v', 'baseline', # פרופיל בסיסי (חובה למכשירים חלשים)
                '-level', '3.0',
                '-preset', 'veryfast',
                '-crf', '24',             # איכות סבירה
                '-c:a', 'aac',            # אודיו מודרני (תואם 235)
                '-b:a', '96k', '-ac', '2', '-ar', '44100',
                final_file
            ], check=True)

        elif mode == 'mp3':
            # פשוט renaming אם כבר ב-MP3
            ext = dl_file.split('.')[-1]
            final_file = f"{uid}_audio.{ext}"
            safe_title += f".{ext}"
            os.rename(dl_file, final_file)
            dl_file = final_file

        else: # רגיל
            final_file = f"{uid}_std.mp4"
            safe_title += ".mp4"
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file, 
                '-c:v', 'libx264', '-profile:v', 'main', 
                '-c:a', 'aac', 
                final_file
            ], check=True)

        # נקיון
        if os.path.exists(dl_file) and dl_file != final_file:
            try: os.remove(dl_file)
            except: pass

        tasks[uid]['file'] = final_file
        tasks[uid]['display'] = safe_title
        tasks[uid]['done'] = True

    except Exception as e:
        tasks[uid]['error'] = str(e)

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start_t():
    d = request.json
    uid = str(uuid.uuid4())
    tasks[uid] = {'percent':0,'done':False,'converting':False}
    threading.Thread(target=process_task, args=(uid, d['url'], d.get('mode','360'))).start()
    return jsonify({'id':uid})

@app.route('/progress/<uid>')
def get_p(uid): return jsonify(tasks.get(uid, {'error':'404'}))

@app.route('/file/<uid>')
def dl(uid):
    t = tasks.get(uid)
    if not t or not t.get('done'): return "Wait", 404
    p = t['file']
    if not os.path.exists(p): return "Gone", 404
    
    n = quote(t.get('display','video.mp4'))
    
    def gen():
        with open(p,'rb') as f:
            while chunk:=f.read(8192): yield chunk
            
    return Response(gen(), headers={"Content-Disposition":f"attachment; filename*=UTF-8''{n}"}, mimetype='application/octet-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
