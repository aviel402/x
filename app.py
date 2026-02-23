import os, threading, uuid, time, subprocess, yt_dlp
from flask import Flask, request, jsonify, send_from_directory, render_template_string

app = Flask(__name__)
tasks = {}

# הגדרות FFmpeg לשרת רנדר
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

# מפת רזולוציות מדויקת
RES_OPTIONS = {
    "144p": "176:144",
    "240p": "320:240", # הגודל של נוקיה
    "360p": "480:360",
    "480p": "640:480"
}

# --- הממשק הגרפי (האתר) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Nokia Converter Cloud</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; text-align: center; padding: 20px; }
        .window { max-width: 500px; margin: auto; border: 2px solid #00ff41; padding: 25px; box-shadow: 0 0 15px #003b00; border-radius: 8px; background: rgba(0,20,0,0.9); }
        h1 { font-size: 24px; border-bottom: 2px solid #00ff41; padding-bottom: 10px; margin-bottom: 25px; }
        input, select, button { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #00ff41; color: #fff; font-family: inherit; font-size: 16px; border-radius: 4px; box-sizing: border-box; }
        button { background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 18px; margin-top: 15px; }
        button:hover { background: #fff; }
        button:disabled { background: #333; color: #777; cursor: not-allowed; }
        .status { margin-top: 20px; font-size: 14px; color: #fff; background: #111; padding: 10px; min-height: 20px; }
        .nokia-badge { background: #003b00; color: #00ff41; padding: 2px 5px; font-size: 10px; vertical-align: middle; border-radius: 3px; border: 1px solid #00ff41; margin-right: 5px; }
    </style>
</head>
<body>
    <div class="window">
        <h1>CLOUD CONVERTER V4.1</h1>
        <input type="text" id="url" placeholder=">> הדבק כאן לינק לסרטון_">
        
        <div style="text-align:right;">
            <label>סוג קובץ:</label>
            <select id="fmt">
                <option value="mp4">VIDEO (MP4)</option>
                <option value="avi">VIDEO (AVI - Retro)</option>
                <option value="3gp">PHONE (3GP - Old Gen)</option>
                <option value="mp3">MUSIC (MP3)</option>
            </select>

            <label>גודל ורזולוציה:</label>
            <select id="res">
                <option value="144p">144p - גודל מזערי</option>
                <option value="240p" selected>240p - גודל אידיאלי (NOKIA)</option>
                <option value="360p">360p - איכות רגילה (SD)</option>
                <option value="480p">480p - איכות גבוהה (HQ)</option>
            </select>
        </div>

        <button onclick="ignite()" id="btn">בצע המרה והורדה</button>
        <div class="status" id="stat">ממתין לפקודה...</div>
    </div>

    <script>
        function ignite() {
            const url = document.getElementById('url').value;
            const fmt = document.getElementById('fmt').value;
            const res = document.getElementById('res').value;
            const btn = document.getElementById('btn');
            const stat = document.getElementById('stat');

            if(!url) return alert("הזן לינק קודם כל!");

            btn.disabled = true;
            stat.innerText = "המתן, השרת מתחבר לענן...";

            fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url, format: fmt, res: res})
            }).then(r => r.json()).then(data => {
                const uid = data.id;
                const poll = setInterval(() => {
                    fetch('/status/' + uid).then(r => r.json()).then(s => {
                        stat.innerText = "סטטוס: " + s.status;
                        if(s.status === "DONE") {
                            clearInterval(poll);
                            stat.innerText = "✅ הושלם! הקובץ יורד מיד...";
                            window.location.href = '/get/' + uid;
                            btn.disabled = false;
                        } else if(s.status.includes("ERR")) {
                            clearInterval(poll);
                            alert(s.status);
                            btn.disabled = false;
                        }
                    });
                }, 2000);
            });
        }
    </script>
</body>
</html>
"""

# --- פונקציית העיבוד ---
def video_worker(uid, url, format_ext, resolution):
    try:
        tasks[uid]['status'] = "מוריד נתונים מהענן..."
        ydl_opts = {
            'outtmpl': f'{uid}_src.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            dl_file = ydl.prepare_filename(info)

        tasks[uid]['status'] = f"ממיר לפורמט {format_ext.upper()}..."
        final_file = f"{uid}_final.{format_ext}"
        scale = RES_OPTIONS.get(resolution, "320:240")

        if format_ext == "mp3":
            cmd = ['ffmpeg', '-y', '-i', dl_file, '-vn', '-ab', '128k', final_file]
        else:
            # הגדרות מיוחדות לפי פורמט
            cmd = ['ffmpeg', '-y', '-i', dl_file, '-vf', f'scale={scale}:force_original_aspect_ratio=decrease,pad={scale.split(":")[0]}:{scale.split(":")[1]}:(ow-iw)/2:(oh-ih)/2']
            if format_ext == "mp4":
                cmd += ['-c:v', 'libx264', '-profile:v', 'baseline', '-c:a', 'aac', '-b:a', '64k', final_file]
            elif format_ext == "avi":
                cmd += ['-c:v', 'mpeg4', '-vtag', 'xvid', '-q:v', '6', '-c:a', 'libmp3lame', final_file]
            elif format_ext == "3gp":
                cmd += ['-s', '176x144', '-r', '15', '-b:v', '100k', '-ac', '1', '-ar', '8000', final_file]

        subprocess.run(cmd, check=True)
        tasks[uid]['file'] = final_file
        tasks[uid]['status'] = "DONE"
        if os.path.exists(dl_file): os.remove(dl_file)
    except Exception as e:
        tasks[uid]['status'] = f"ERR: {str(e)}"

# --- נתיבים (Routes) ---

@app.route('/')
def index(): return render_template_string(HTML_PAGE)

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    uid = str(uuid.uuid4())
    tasks[uid] = {'status': 'התחלה...', 'timestamp': time.time()}
    threading.Thread(target=video_worker, args=(uid, data['url'], data['format'], data['res'])).start()
    return jsonify({'id': uid})

@app.route('/status/<uid>')
def status(uid): return jsonify(tasks.get(uid, {'status': 'Missing'}))

@app.route('/get/<uid>')
def get_file(uid):
    task = tasks.get(uid)
    if task and task['status'] == 'DONE':
        return send_from_directory('.', task['file'], as_attachment=True)
    return "Error", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
