import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time, sys
from urllib.parse import quote

# --- FFmpeg Setup ---
# וידוא שנתיב הבינאריים זמין למערכת
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

# --- עיצוב חדש: Windows 95 Vaporwave ---
HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>Nokia Converter 95</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* עיצוב וינדוס 95 */
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
    font-family: inherit;
}

button.primary {
    width: 100%; padding: 8px;
    background: #c0c0c0;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    font-weight: bold; cursor: pointer; color: black;
    margin-top: 10px;
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

/* Custom Checkbox 95 Style */
.checkbox-row {
    display: flex; align-items: center; margin-top: 10px;
    background: #fff; border: 2px inset #dfdfdf; padding: 5px;
}
input[type="checkbox"] {
    width: auto; margin-left: 10px;
}

img.thumb {
    width: 100%; border: 2px inset #dfdfdf; margin-top: 10px; display: none;
}

.hidden { display: none; }
</style>
</head>
<body>

<div class="window">
    <div class="title-bar">
        <span>Nokia Cloud Converter.exe</span>
        <div class="title-bar-controls">
            <button aria-label="Minimize">_</button>
            <button aria-label="Maximize">□</button>
            <button aria-label="Close">X</button>
        </div>
    </div>
    
    <div class="window-body">
        <fieldset>
            <legend>Input Source</legend>
            <label>YouTube / TikTok URL:</label>
            <input type="text" id="url" placeholder="http://...">
        </fieldset>

        <fieldset>
            <legend>Settings</legend>
            <label>Format:</label>
            <select id="mode">
                <option value="360">Video (MP4 Standard)</option>
                <option value="mp3">Audio Only (MP3)</option>
            </select>
            
            <div class="checkbox-row">
                <input type="checkbox" id="nokiaSwitch" checked>
                <label for="nokiaSwitch" style="font-weight:bold;">Retro Mode (AVI / 240p)</label>
            </div>
        </fieldset>

        <button class="primary" onclick="start()" id="btn">Start Download</button>

        <img id="thumb" class="thumb">
        <div id="videoTitle" style="font-size:12px; margin-top:5px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;"></div>

        <div class="progress-track" id="progContainer">
            <div class="progress-fill" id="bar"></div>
        </div>
        
        <div class="status-bar">
            <span id="statusText">Ready</span>
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
    const nokia = document.getElementById('nokiaSwitch').checked;
    
    if(!url) return alert("Error: Please enter a valid URL.");

    document.getElementById('btn').disabled = true;
    document.getElementById('statusText').innerText = "Connecting...";
    document.getElementById('progContainer').style.display = "block";
    document.getElementById('bar').style.width = "0%";
    
    fetch('/start', {
        method: 'POST', 
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({url:url, mode:mode, nokia:nokia})
    })
    .then(r => r.json())
    .then(d => {
        if(d.error) throw d.error;
        id = d.id;
        interval = setInterval(check, 1500);
    })
    .catch(e => {
        alert("System Error: " + e);
        reset();
    });
}

function check() {
    fetch('/progress/' + id).then(r => r.json()).then(d => {
        if(d.error) {
            clearInterval(interval);
            alert("Process Failed: " + d.error);
            reset();
            return;
        }

        // Visual updates
        document.getElementById('bar').style.width = d.percent + "%";
        document.getElementById('percentText').innerText = d.percent + "%";
        
        if(d.title) document.getElementById('videoTitle').innerText = d.title;
        if(d.thumb && document.getElementById('thumb').style.display === "none") {
            document.getElementById('thumb').src = d.thumb;
            document.getElementById('thumb').style.display = "block";
        }

        let txt = "Downloading...";
        if(d.converting) txt = d.mode === 'nokia' ? "Converting to Nokia (AVI)..." : "Processing MP4...";
        if(d.done) txt = "Done.";
        
        document.getElementById('statusText').innerText = txt;

        if(d.done) {
            clearInterval(interval);
            window.location.href = '/file/' + id;
            reset();
            document.getElementById('statusText').innerText = "File Saved.";
        }
    });
}

function reset() {
    document.getElementById('btn').disabled = false;
}
</script>
</body>
</html>
"""

def process_task(uid, url, mode_val, is_nokia):
    try:
        tasks[uid]['timestamp'] = time.time()

        # עוקף חסימות (הגדרת לקוח אנדרואיד)
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android']}}
        }

        if mode_val == 'mp3' and not is_nokia:
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
            
            # איתור הקובץ שהורד
            temp_name = ydl.prepare_filename(info)
            if os.path.exists(temp_name): dl_file = temp_name
            else:
                for f in os.listdir('.'):
                    if f.startswith(f"{uid}_src"):
                        dl_file = f
                        break
        
        if not dl_file: raise Exception("Download failed (File missing)")

        # הכנת שם סופי
        safe_title = "".join([c for c in info.get('title','file') if c.isalnum() or c in ' -_']).strip()
        final_file = f"{uid}_done"
        
        # --- Nokia / Retro Mode (AVI) ---
        if is_nokia and mode_val != 'mp3':
            final_file += ".avi"
            safe_title += ".avi"
            # פקודת FFmpeg שתמיד עובדת לנוקיה (MPEG4 + MP3)
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20', '-c:v', 'mpeg4', '-vtag', 'xvid', '-q:v', '6',
                '-c:a', 'libmp3lame', '-ac', '1', '-ar', '24000', '-b:a', '64k',
                final_file
            ], check=True)
            
        elif mode_val == 'mp3':
            final_file += ".mp3"
            safe_title += ".mp3"
            # רק שינוי שם
            if dl_file.endswith('.mp3'):
                os.rename(dl_file, final_file)
            else:
                # המרה אם צריך
                subprocess.run(['ffmpeg', '-y', '-i', dl_file, '-c:a', 'libmp3lame', final_file], check=True)

        else:
            final_file += ".mp4"
            safe_title += ".mp4"
            # המרה זריזה ל-MP4 ליתר ביטחון
            subprocess.run(['ffmpeg', '-y', '-i', dl_file, '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', final_file], check=True)

        # מחיקת קובץ המקור
        if os.path.exists(dl_file) and dl_file != final_file:
            try: os.remove(dl_file)
            except: pass

        tasks[uid]['file'] = final_file
        tasks[uid]['display'] = safe_title
        tasks[uid]['done'] = True

    except Exception as e:
        tasks[uid]['error'] = str(e)

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start_download():
    data = request.json
    uid = str(uuid.uuid4())
    tasks[uid] = {'percent':0, 'done':False, 'mode':data.get('mode')}
    
    threading.Thread(target=process_task, args=(uid, data['url'], data['mode'], data['nokia'])).start()
    return jsonify({'id': uid})

@app.route('/progress/<uid>')
def progress(uid):
    return jsonify(tasks.get(uid, {'error': 'Not found'}))

@app.route('/file/<uid>')
def serve_file(uid):
    task = tasks.get(uid)
    if not task or not task.get('done'): return "Not Ready", 404
    
    path = task['file']
    if not os.path.exists(path): return "Error", 404
    
    dname = quote(task.get('display', 'video'))
    
    def generate():
        with open(path, "rb") as f:
            while chunk := f.read(4096):
                yield chunk
    
    return Response(generate(), headers={"Content-Disposition": f"attachment; filename*=UTF-8''{dname}"})

if __name__ == '__main__':
    # זה התיקון הקריטי ל-502 - שימוש בפורט של הסביבה
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
