import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time, sys
from urllib.parse import quote

# הגדרות שרת
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

app = Flask(__name__)
tasks = {}
# הגבלת הורדות מקבילות (למניעת קריסת השרת)
download_semaphore = threading.Semaphore(3)

def cleanup_loop():
    """מנקה קבצים ישנים מעל 20 דקות"""
    while True:
        try:
            current_time = time.time()
            for uid, task in list(tasks.items()):
                if current_time - task.get('timestamp', 0) > 1200:
                    fpath = task.get('file')
                    if fpath and os.path.exists(fpath):
                        try: os.remove(fpath)
                        except: pass
                    tasks.pop(uid, None)
        except Exception as e:
            print(f"Cleanup error: {e}")
        time.sleep(60)

threading.Thread(target=cleanup_loop, daemon=True).start()

# --- עיצוב משופר (CSS Grid + Neon Glow) ---
HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>CYBER-NOKIA LINK v2</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    :root {
        --neon-blue: #00f3ff;
        --neon-pink: #bc13fe;
        --dark-bg: #05050a;
    }
    body {
        background: var(--dark-bg);
        color: var(--neon-blue);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: flex; justify-content: center; align-items: center;
        min-height: 100vh; margin: 0;
        overflow: hidden;
    }
    .cyber-card {
        background: rgba(10, 10, 20, 0.9);
        border: 2px solid var(--neon-blue);
        padding: 40px;
        border-radius: 5px;
        box-shadow: 0 0 20px var(--neon-blue);
        width: 90%; max-width: 450px;
        text-align: center;
    }
    input, select {
        width: 100%; padding: 12px; margin: 10px 0;
        background: #000; border: 1px solid var(--neon-pink);
        color: #fff; border-radius: 3px; box-sizing: border-box;
    }
    button {
        width: 100%; padding: 15px;
        background: var(--neon-blue); color: #000;
        font-weight: bold; border: none; cursor: pointer;
        transition: 0.3s; text-transform: uppercase;
    }
    button:hover { background: var(--neon-pink); color: white; }
    .console {
        margin-top: 20px; background: #000;
        height: 120px; overflow-y: auto;
        font-family: monospace; font-size: 12px;
        text-align: left; padding: 10px; border: 1px solid #333;
    }
    .progress-bar { height: 5px; background: #222; margin-top: 10px; }
    .progress-fill { height: 100%; width: 0%; background: var(--neon-pink); transition: 0.3s; }
</style>
</head>
<body>
    <div class="cyber-card">
        <h2>NOKIA SYNC <small style="font-size: 10px;">V2.1</small></h2>
        <input type="text" id="url" placeholder="הכנס קישור ליוטיוב...">
        <select id="mode">
            <option value="nokia">Nokia 235 (3GP/MP4 240p)</option>
            <option value="mp3">Audio Extraction (MP3)</option>
            <option value="360">Standard MP4 (360p)</option>
        </select>
        <button onclick="start()" id="btn">INITIALIZE LINK</button>
        <div class="console" id="console" style="display:none;">
            <div id="log"></div>
            <div class="progress-bar"><div class="progress-fill" id="bar"></div></div>
        </div>
    </div>

    <script>
        let tid;
        function log(m) { 
            const l = document.getElementById('log');
            l.innerHTML = `> ${m}<br>` + l.innerHTML;
        }

        async function start() {
            const url = document.getElementById('url').value;
            if(!url) return;
            
            document.getElementById('btn').disabled = true;
            document.getElementById('console').style.display = 'block';
            log("מתחיל סנכרון...");

            const res = await fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url, mode: document.getElementById('mode').value})
            });
            const data = await res.json();
            tid = data.id;
            const interval = setInterval(async () => {
                const pReq = await fetch('/progress/' + tid);
                const p = await pReq.json();
                
                if(p.percent) document.getElementById('bar').style.width = p.percent + '%';
                if(p.converting) log("מבצע המרה פרוטוקולית...");
                
                if(p.done) {
                    clearInterval(interval);
                    log("הושלם!");
                    document.getElementById('btn').innerText = "הורד קובץ";
                    document.getElementById('btn').disabled = false;
                    document.getElementById('btn').onclick = () => window.location.href = '/file/' + tid;
                }
                if(p.error) {
                    clearInterval(interval);
                    log("שגיאה: " + p.error);
                }
            }, 1500);
        }
    </script>
</body>
</html>
"""

def processing_task(uid, url, mode):
    with download_semaphore:
        try:
            tasks[uid]['timestamp'] = time.time()
            
            # הגדרות הורדה
            src_path = os.path.join(DOWNLOAD_DIR, f"{uid}_src")
            ydl_opts = {
                'quiet': True,
                'outtmpl': src_path + '.%(ext)s',
                'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                'merge_output_format': 'mp4',
                'nocheckcertificate': True,
            }

            if mode == 'mp3':
                ydl_opts['format'] = 'bestaudio/best'

            def hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%','')
                        tasks[uid]['percent'] = int(float(p)) * 0.7 # 70% להורדה
                    except: pass

            ydl_opts['progress_hooks'] = [hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ext = info.get('ext', 'mp4')
                downloaded_file = f"{src_path}.{ext}"
                title = info.get('title', 'video')

            tasks[uid]['converting'] = True
            final_file = os.path.join(DOWNLOAD_DIR, f"{uid}_final")

            # --- עיבוד FFmpeg מקצועי ---
            if mode == 'nokia':
                final_file += ".mp4"
                cmd = [
                    'ffmpeg', '-y', '-i', downloaded_file,
                    '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
                    '-r', '15', '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
                    '-c:a', 'aac', '-b:a', '64k', '-ac', '1', '-ar', '32000', final_file
                ]
            elif mode == 'mp3':
                final_file += ".mp3"
                cmd = ['ffmpeg', '-y', '-i', downloaded_file, '-vn', '-c:a', 'libmp3lame', '-q:a', '4', final_file]
            else:
                final_file += ".mp4"
                cmd = ['ffmpeg', '-y', '-i', downloaded_file, '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', final_file]

            subprocess.run(cmd, check=True, timeout=300)

            # ניקוי מקור
            if os.path.exists(downloaded_file): os.remove(downloaded_file)

            tasks[uid].update({
                'file': final_file,
                'display': title,
                'percent': 100,
                'done': True
            })

        except Exception as e:
            tasks[uid]['error'] = str(e)

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start_task():
    data = request.json
    uid = str(uuid.uuid4())
    tasks[uid] = {'percent': 0, 'done': False, 'converting': False, 'timestamp': time.time()}
    threading.Thread(target=processing_task, args=(uid, data['url'], data['mode'])).start()
    return jsonify({'id': uid})

@app.route('/progress/<uid>')
def progress(uid): return jsonify(tasks.get(uid, {'error': 'Not Found'}))

@app.route('/file/<uid>')
def get_file(uid):
    task = tasks.get(uid)
    if not task or not task.get('done'): return "File not ready", 404
    
    file_path = task['file']
    safe_name = quote(f"{task['display']}.{file_path.split('.')[-1]}")
    
    return Response(
        open(file_path, 'rb'),
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
        mimetype='application/octet-stream'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
