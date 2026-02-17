import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time, sys
from urllib.parse import quote

# --- FFmpeg Configuration ---
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

app = Flask(__name__)
tasks = {}

# --- מנקה זיכרון אוטומטי ---
def cleanup_loop():
    while True:
        try:
            current_time = time.time()
            to_delete = []
            for uid, task in list(tasks.items()):
                # מחיקה אחרי 15 דקות
                if current_time - task.get('timestamp', 0) > 900:
                    fpath = task.get('file')
                    if fpath and os.path.exists(fpath):
                        try: os.remove(fpath)
                        except: pass
                    # מחיקת קבצי זבל
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

# --- עיצוב: Windows 95 Vaporwave ---
HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>Nokia Converter 95</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* עיצוב וינדוס 95 מדויק */
body {
    background-color: #008080;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; margin: 0; padding: 10px;
}

.window {
    width: 100%; max-width: 450px;
    background-color: #c0c0c0;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    box-shadow: 4px 4px 0px rgba(0,0,0,0.5);
    padding: 2px;
}

.title-bar {
    background: linear-gradient(90deg, #000080, #1084d0);
    padding: 4px 8px;
    display: flex; justify-content: space-between; align-items: center;
    color: white; font-weight: bold; letter-spacing: 0.5px;
}

.title-bar-controls button {
    width: 16px; height: 16px;
    background: #c0c0c0;
    border: 1px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    font-size: 10px; line-height: 12px; font-weight: bold;
    margin-left: 2px; padding: 0;
}

.window-body { padding: 16px; text-align: right; }

fieldset {
    border: 2px groove #dfdfdf;
    padding: 10px; margin-bottom: 15px;
}

legend { margin-right: 10px; padding: 0 5px; }

input, select {
    width: 100%; box-sizing: border-box;
    padding: 5px; margin-top: 5px;
    border: 2px inset #dfdfdf;
    background: #fff;
    font-family: inherit; font-size: 14px;
}

button.primary {
    width: 100%; padding: 8px;
    background: #c0c0c0;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    font-weight: bold; cursor: pointer; color: black;
    margin-top: 10px; font-size: 14px;
}

button.primary:active {
    border-color: #808080 #ffffff #ffffff #808080;
    transform: translate(1px, 1px);
}

button:disabled { color: #808080; text-shadow: 1px 1px #fff; cursor: wait; }

/* Status Bar & Progress */
.status-bar {
    margin-top: 15px;
    border: 2px inset #dfdfdf;
    background: #c0c0c0;
    padding: 4px;
    display: flex; justify-content: space-between;
    font-size: 13px;
}

.progress-track {
    margin-top: 10px;
    background: #fff;
    border: 2px inset #dfdfdf;
    height: 18px;
    position: relative;
    display: none;
}

.progress-fill {
    height: 100%; width: 0%;
    background: #000080;
    transition: width 0.3s;
}

img.thumb {
    width: 100%; border: 2px inset #dfdfdf; margin-top: 10px; display: none;
}
</style>
</head>
<body>

<div class="window">
    <div class="title-bar">
        <span>Nokia Converter 95.exe</span>
        <div class="title-bar-controls">
            <button>_</button><button>□</button><button>X</button>
        </div>
    </div>
    
    <div class="window-body">
        <fieldset>
            <legend>Multimedia Source</legend>
            <label>YouTube / TikTok Link:</label>
            <input type="text" id="url" placeholder="http://...">
        </fieldset>

        <fieldset>
            <legend>Format Selection</legend>
            <label>Output Type:</label>
            <select id="mode">
                <option value="360">Video Standard (MP4 / 360p)</option>
                <option value="mp3">Audio Only (MP3)</option>
                <option value="nokia">NOKIA 3310 Mode (AVI / 240p)</option>
            </select>
        </fieldset>

        <button class="primary" onclick="start()" id="btn">Initialize Download</button>

        <img id="thumb" class="thumb">
        <div id="videoTitle" style="font-size:12px; margin-top:5px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;"></div>

        <div class="progress-track" id="progContainer">
            <div class="progress-fill" id="bar"></div>
        </div>
        
        <div class="status-bar">
            <span id="statusText">System Ready</span>
            <span id="percentText">0%</span>
        </div>
    </div>
</div>

<script>
let id = null;
let interval = null;

function start() {
    const url = document.getElementById('url').value;
    const mode = document.getElementById('mode').value;
    
    if(!url) return alert("Error: URL Field is empty.");

    // UI Updates
    document.getElementById('btn').disabled = true;
    document.getElementById('btn').innerText = "Processing...";
    document.getElementById('statusText').innerText = "Connecting to server...";
    document.getElementById('progContainer').style.display = "block";
    document.getElementById('bar').style.width = "0%";
    
    fetch('/start', {
        method: 'POST', 
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({url:url, mode:mode})
    })
    .then(r => r.json())
    .then(d => {
        if(d.error) throw d.error;
        id = d.id;
        interval = setInterval(check, 1000);
    })
    .catch(e => {
        alert("Server Error: " + e);
        reset();
    });
}

function check() {
    if(!id) return;
    fetch('/progress/' + id).then(r => r.json()).then(d => {
        if(d.error) {
            clearInterval(interval);
            document.getElementById('statusText').innerText = "Failed.";
            alert("Error: " + d.error);
            reset();
            return;
        }

        // Visual updates
        document.getElementById('bar').style.width = d.percent + "%";
        document.getElementById('percentText').innerText = d.percent + "%";
        
        if(d.title) document.getElementById('videoTitle').innerText = d.title.substring(0,50);
        if(d.thumb && document.getElementById('thumb').style.display === "none") {
            document.getElementById('thumb').src = d.thumb;
            document.getElementById('thumb').style.display = "block";
        }

        let txt = "Downloading stream...";
        if(d.converting) txt = "Converting format...";
        if(d.done) txt = "Completed.";
        
        document.getElementById('statusText').innerText = txt;

        if(d.done) {
            clearInterval(interval);
            window.location.href = '/file/' + id;
            document.getElementById('btn').innerText = "Download Finished";
            setTimeout(reset, 2000);
        }
    }).catch(e => console.log(e));
}

function reset() {
    document.getElementById('btn').disabled = false;
    document.getElementById('btn').innerText = "Initialize Download";
}
</script>
</body>
</html>
"""

def process_task(uid, url, mode_input):
    try:
        tasks[uid]['timestamp'] = time.time()

        # הגדרות לקוח לעקיפת חסימות יוטיוב
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            # מנסה למצוא פורמט קיים ללא המרה כדי למנוע חסימה, אם לא אז הכי טוב עד 360
            'format': 'best[height<=360]/best',
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'], # אנדרואיד עוקף הכי טוב כרגע
                }
            }
        }

        if mode_input == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

        def progress_hook(d):
            if d['status'] == 'downloading':
                try: 
                    p = d.get('_percent_str', '0%').replace('%', '')
                    tasks[uid]['percent'] = int(float(p))
                except: pass
            if d['status'] == 'finished':
                tasks[uid]['percent'] = 99
                tasks[uid]['converting'] = True

        ydl_opts['progress_hooks'] = [progress_hook]

        info = None
        dl_file = None
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            tasks[uid]['title'] = info.get('title', 'Video')
            tasks[uid]['thumb'] = info.get('thumbnail')
            
            # חיפוש הקובץ שהורד
            temp_name = ydl.prepare_filename(info)
            # יש באג ב-yt-dlp שלפעמים שם הקובץ משתנה אחרי המרה, אז נחפש לפי קידומת
            if os.path.exists(temp_name):
                 dl_file = temp_name
            else:
                 # fallback scan
                 for f in os.listdir('.'):
                     if f.startswith(f"{uid}_src"):
                         dl_file = f
                         break
        
        if not dl_file or not os.path.exists(dl_file): 
            raise Exception("File not found on server")

        # --- שלב ההמרה ---
        safe_title = "".join([c for c in info.get('title','file') if c.isalnum() or c in ' -_']).strip()
        final_file = ""
        
        # 1. מצב נוקיה (AVI)
        if mode_input == 'nokia':
            final_file = f"{uid}_nokia.avi"
            safe_title += ".avi"
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '15',                 # פריימים נמוכים מאוד
                '-c:v', 'mpeg4',            # קודק XviD/MPEG4
                '-vtag', 'xvid',
                '-q:v', '9',                # איכות בינונית
                '-c:a', 'libmp3lame',       # MP3 אודיו
                '-ac', '1',                 # מונו
                '-ar', '22050',
                '-b:a', '48k',
                final_file
            ], check=True)

        # 2. מצב MP3
        elif mode_input == 'mp3':
            # yt-dlp כבר עשה את רוב העבודה, רק משנים שם אם צריך
            ext = dl_file.split('.')[-1]
            final_file = f"{uid}_audio.{ext}"
            safe_title += f".{ext}"
            os.rename(dl_file, final_file)
            dl_file = final_file # מונע מחיקה בטעות למטה

        # 3. וידאו רגיל (360)
        else:
            final_file = f"{uid}_video.mp4"
            safe_title += ".mp4"
            # מוודאים שזה MP4 תקין
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file, 
                '-c:v', 'libx264', '-preset', 'veryfast', 
                '-c:a', 'aac', 
                final_file
            ], check=True)

        # ניקוי מקור אם נוצר קובץ חדש
        if os.path.exists(dl_file) and dl_file != final_file:
            try: os.remove(dl_file)
            except: pass

        tasks[uid]['file'] = final_file
        tasks[uid]['display'] = safe_title
        tasks[uid]['done'] = True

    except Exception as e:
        print(f"ERROR TASK {uid}: {e}")
        tasks[uid]['error'] = str(e)

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start_download():
    data = request.json
    uid = str(uuid.uuid4())
    # data['mode'] יכול להיות: '360', 'mp3', 'nokia'
    mode = data.get('mode', '360')
    
    tasks[uid] = {'percent':0, 'done':False, 'mode':mode, 'error':None}
    
    threading.Thread(target=process_task, args=(uid, data['url'], mode)).start()
    return jsonify({'id': uid})

@app.route('/progress/<uid>')
def progress(uid):
    return jsonify(tasks.get(uid, {'error': 'Not found'}))

@app.route('/file/<uid>')
def serve_file(uid):
    task = tasks.get(uid)
    if not task or not task.get('done'): return "Not Ready", 404
    
    path = task.get('file')
    if not path or not os.path.exists(path): return "File missing", 404
    
    # שם הקובץ שיראה המשתמש
    dname = task.get('display', 'download')
    try:
        encoded_name = quote(dname)
    except:
        encoded_name = "file"
    
    def generate():
        with open(path, "rb") as f:
            while chunk := f.read(4096):
                yield chunk
    
    # כאן היה השגיאה קודם - עכשיו הקוד תקין ומלא
    return Response(
        generate(),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
