import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time, sys
from urllib.parse import quote

# --- בדיקת FFmpeg ---
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

app = Flask(__name__)
tasks = {}

# --- ניקוי זיכרון וקבצים ---
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

# --- עיצוב: NEON CYBERPUNK ---
HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CYBER-NOKIA LINK</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Teko:wght@300;500;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    :root {
        --neon-blue: #00f3ff;
        --neon-pink: #bc13fe;
        --dark-bg: #020205;
        --glass: rgba(10, 10, 20, 0.7);
    }

    body {
        background-color: var(--dark-bg);
        color: var(--neon-blue);
        font-family: 'Share Tech Mono', monospace;
        margin: 0; min-height: 100vh;
        display: flex; justify-content: center; align-items: center;
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(188, 19, 254, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        overflow-x: hidden;
    }

    /* Scanlines effect */
    body::after {
        content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
        background-size: 100% 4px; z-index: 0; pointer-events: none;
    }

    .cyber-card {
        width: 100%; max-width: 500px;
        background: var(--glass);
        border: 1px solid var(--neon-blue);
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
        padding: 30px;
        position: relative;
        z-index: 1;
        clip-path: polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%);
    }

    .cyber-card::before {
        content: ''; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px;
        z-index: -1;
        background: linear-gradient(45deg, var(--neon-blue), transparent, var(--neon-pink));
        clip-path: polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%);
    }

    h1 {
        font-family: 'Teko', sans-serif;
        font-size: 40px; margin: 0; line-height: 1;
        text-transform: uppercase;
        background: linear-gradient(90deg, #fff, var(--neon-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
    }

    .tagline {
        color: var(--neon-pink);
        font-size: 12px; letter-spacing: 2px;
        margin-bottom: 25px; display: block;
        text-transform: uppercase;
    }

    .input-group { position: relative; margin-bottom: 20px; }

    input, select {
        width: 100%;
        background: rgba(0,0,0,0.8);
        border: 1px solid #333;
        border-left: 3px solid var(--neon-blue);
        padding: 15px; color: #fff;
        font-family: 'Share Tech Mono', monospace;
        font-size: 16px;
        box-sizing: border-box;
        transition: 0.3s;
        outline: none;
    }

    input:focus, select:focus {
        border-color: var(--neon-blue);
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    }

    button {
        width: 100%;
        padding: 15px;
        background: var(--neon-blue);
        color: #000;
        font-family: 'Teko', sans-serif;
        font-size: 24px; letter-spacing: 1px;
        border: none;
        cursor: pointer;
        text-transform: uppercase;
        clip-path: polygon(0 0, 100% 0, 100% 80%, 95% 100%, 0 100%);
        transition: 0.3s;
        font-weight: 700;
    }

    button:hover {
        background: var(--neon-pink);
        color: #fff;
        box-shadow: 0 0 20px var(--neon-pink);
    }

    button:disabled {
        background: #333; color: #777;
        cursor: not-allowed; box-shadow: none;
    }

    .console {
        background: #000;
        border: 1px solid #333;
        padding: 10px; margin-top: 20px;
        font-size: 12px; height: 100px;
        overflow-y: auto; display: none;
        color: #0f0;
    }

    .progress-bar {
        height: 4px; background: #333;
        margin-top: 5px; position: relative;
    }
    
    .progress-fill {
        position: absolute; left: 0; top: 0; bottom: 0;
        width: 0%; background: var(--neon-blue);
        box-shadow: 0 0 10px var(--neon-blue);
        transition: width 0.3s;
    }
</style>
</head>
<body>

<div class="cyber-card">
    <h1>NOKIA SYNC</h1>
    <span class="tagline">Protocol 235 // Neural Link V2.1</span>

    <div class="input-group">
        <input type="text" id="url" placeholder=">> INSERT TARGET URL_">
    </div>

    <div class="input-group">
        <select id="mode">
            <option value="nokia">MODE: NOKIA 235 (MP4 240p)</option>
            <option value="mp3">MODE: AUDIO EXTRACTION (MP3)</option>
            <option value="360">MODE: STANDARD (MP4 360p)</option>
        </select>
    </div>

    <button onclick="startSequence()" id="btn">INITIALIZE</button>

    <div class="console" id="console">
        <div id="log-text"></div>
        <div class="progress-bar"><div class="progress-fill" id="bar"></div></div>
    </div>
</div>

<script>
let id = null;
let matrix = null;

function log(msg) {
    const l = document.getElementById('log-text');
    l.innerHTML = `> ${msg}<br>` + l.innerHTML;
}

function startSequence(){
    const url = document.getElementById('url').value;
    const mode = document.getElementById('mode').value;
    
    if(!url) return alert("TARGET MISSING");

    document.getElementById('btn').disabled = true;
    document.getElementById('btn').innerText = "RUNNING...";
    document.getElementById('console').style.display = 'block';
    document.getElementById('log-text').innerHTML = "";
    log("SYSTEM STARTED...");
    
    fetch('/start', {
        method: 'POST', 
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({url:url, mode:mode})
    })
    .then(r => r.json())
    .then(d => {
        if(d.error) throw d.error;
        id = d.id;
        matrix = setInterval(updateMatrix, 1000);
    })
    .catch(e => {
        log("CRITICAL ERROR: " + e);
        document.getElementById('btn').disabled = false;
        document.getElementById('btn').innerText = "RETRY";
    });
}

function updateMatrix(){
    if(!id) return;
    fetch('/progress/'+id).then(r=>r.json()).then(d=>{
        
        if(d.error) {
            clearInterval(matrix);
            log("ERROR: " + d.error);
            document.getElementById('btn').disabled = false;
            document.getElementById('btn').innerText = "RETRY";
            return;
        }

        document.getElementById('bar').style.width = d.percent + '%';

        let status = "DL: " + d.percent + "%";
        if(d.converting) status = "TRANSCODING FLUX >> " + d.mode;
        if(d.done) status = "DONE. FILE READY.";
        
        // מונע הצפת לוגים - מעדכן רק אם יש שינוי משמעותי
        if(document.getElementById('log-text').innerHTML.indexOf(status) === -1) {
            log(status);
        }

        if(d.done) {
            clearInterval(matrix);
            document.getElementById('btn').innerHTML = "DOWNLOAD FILE";
            document.getElementById('btn').disabled = false;
            document.getElementById('btn').onclick = function() {
                window.location.href = '/file/'+id;
            };
            window.location.href = '/file/'+id; // Auto DL
        }

    }).catch(e => console.log(e));
}
</script>
</body>
</html>
"""

def processing_task(uid, url, mode):
    try:
        tasks[uid]['timestamp'] = time.time()
        
        # --- הגדרת הורדה מנצחת ---
        # 1. מוותרים על חיפוש גודל ספציפי (height<=360) כדי לא להיכשל.
        # 2. מורידים וידאו + אודיו הכי טובים ש-ydl מוצא.
        # 3. ממזגים הכל (merge_output_format) כדי לקבל קובץ אחד תקין.
        # 4. הכיווץ לנוקיה יקרה אצלנו, לא ביוטיוב.
        
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            'format': 'bestvideo+bestaudio/best', # מוריד הכי טוב וממזג
            'merge_output_format': 'mp4',        # מכריח מיזוג ל-mp4
            'nocheckcertificate': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        }

        if mode == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

        def progress_hook(d):
            if d['status'] == 'downloading':
                try: 
                    p = d.get('_percent_str', '0%').replace('%','')
                    tasks[uid]['percent'] = int(float(p))
                except: pass
            if d['status'] == 'finished':
                tasks[uid]['percent'] = 50 # סימן שההורדה נגמרה ומתחילים להמיר
                tasks[uid]['converting'] = True

        ydl_opts['progress_hooks'] = [progress_hook]

        info = None
        dl_file = None
        
        # שלב 1: הורדה אגרסיבית (בלי הגבלות איכות)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                tasks[uid]['title'] = info.get('title', 'Unknown_File')
                
                # מציאת הקובץ (יכול להיות שיהיה .mkv או .webm לפני המרה)
                base_name = ydl.prepare_filename(info)
                
                # בגלל שהשתמשנו ב-merge_output_format=mp4, נחפש ספציפית
                # לפעמים השם המקורי שונה ממה שנוצר, אז נחפש קובץ עם ה-UID
                for f in os.listdir('.'):
                    if f.startswith(f"{uid}_src"):
                        dl_file = f
                        break
                        
            except Exception as e:
                # Fallback למקרה של "Format Not Available" עדיין
                # מנסים את ה"כי פשוט" (בלי מיזוג)
                print(f"First try failed: {e}, retrying basic...")
                ydl_opts['format'] = 'best' # הכי פשוט שיש
                info = ydl.extract_info(url, download=True)
                dl_file = ydl.prepare_filename(info)

        if not dl_file or not os.path.exists(dl_file):
            raise Exception("Critical: Source file not created.")

        tasks[uid]['percent'] = 75
        
        # שלב 2: עיבוד וכיווץ (FFmpeg)
        safe_title = "".join([c for c in info.get('title','v') if c.isalnum() or c in ' -_']).strip()
        final_file = ""
        
        # === Nokia 235 Profile (S30+) ===
        if mode == 'nokia':
            final_file = f"{uid}_nokia.mp4"
            safe_title += "_nokia.mp4"
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20',               # Framerate
                '-c:v', 'libx264',        # H.264 
                '-profile:v', 'baseline', # Baseline profile (חיוני!)
                '-level', '3.0',
                '-preset', 'fast',
                '-crf', '26',             # דחיסה טובה (קובץ קטן)
                '-c:a', 'aac',            # AAC Audio
                '-b:a', '64k', '-ac', '1', '-ar', '44100',
                final_file
            ], check=True)
            
        elif mode == 'mp3':
            # ההמרה ל-MP3 נעשתה ע"י yt-dlp אם אפשר, או שנמיר כאן
            ext = dl_file.split('.')[-1]
            if ext == 'mp3':
                final_file = f"{uid}.mp3"
                os.rename(dl_file, final_file)
            else:
                final_file = f"{uid}.mp3"
                subprocess.run(['ffmpeg', '-y', '-i', dl_file, '-c:a', 'libmp3lame', '-q:a', '2', final_file], check=True)
            safe_title += ".mp3"

        else: # Standard MP4
            final_file = f"{uid}.mp4"
            safe_title += ".mp4"
            # רק מוודאים המרה ל-MP4
            if dl_file.endswith(".mp4"):
                os.rename(dl_file, final_file)
            else:
                subprocess.run(['ffmpeg','-y','-i',dl_file,'-c:v','libx264','-c:a','aac',final_file], check=True)

        # נקיון
        if os.path.exists(dl_file) and dl_file != final_file:
            try: os.remove(dl_file)
            except: pass

        tasks[uid]['file'] = final_file
        tasks[uid]['display'] = safe_title
        tasks[uid]['percent'] = 100
        tasks[uid]['done'] = True
        tasks[uid]['mode'] = mode

    except Exception as e:
        print(f"FATAL TASK ERROR {uid}: {e}")
        tasks[uid]['error'] = str(e)

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def s():
    d = request.json
    uid = str(uuid.uuid4())
    tasks[uid] = {'percent':0,'done':False,'converting':False}
    threading.Thread(target=processing_task, args=(uid, d['url'], d['mode'])).start()
    return jsonify({'id':uid})

@app.route('/progress/<uid>')
def p(uid): return jsonify(tasks.get(uid, {'error':'Not Found'}))

@app.route('/file/<uid>')
def f(uid):
    t = tasks.get(uid)
    if not t or not t.get('done'): return "Wait", 404
    p = t['file']
    if not os.path.exists(p): return "Missing", 404
    
    n = quote(t.get('display','file.bin'))
    def g():
        with open(p,'rb') as f:
            while c:=f.read(8192): yield c
    return Response(g(), headers={"Content-Disposition":f"attachment; filename*=UTF-8''{n}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
