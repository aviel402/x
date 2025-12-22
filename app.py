from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, sys

# --- קריטי ל-Render: הוספת FFmpeg לנתיב המערכת ---
# אנו מוודאים שהשרת מכיר את התיקייה שבה התקנו את FFmpeg
os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")
# ---------------------------------------------------

app = Flask(__name__)
tasks = {}

HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>Nokia Render Converter</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;min-height:100vh;display:flex;justify-content:center;align-items:center;background:radial-gradient(circle at top,#1a1a2e,#16213e);font-family:'Segoe UI',Arial;color:white}
.box{width:90%;max-width:450px;padding:25px;border-radius:16px;background:rgba(255,255,255,.05);backdrop-filter:blur(10px);box-shadow:0 8px 32px rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1)}
h2{text-align:center;margin-top:0;color:#4cc9f0}
input,select,button{width:100%;padding:14px;margin:8px 0;border:none;border-radius:8px;font-size:16px;box-sizing:border-box}
input,select{background:rgba(255,255,255,0.1);color:white;outline:none}
button{background:linear-gradient(45deg,#4cc9f0,#4361ee);color:white;font-weight:bold;cursor:pointer;transition:0.3s}
button:disabled{opacity:0.6;cursor:not-allowed}
.switch-container{display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,0.05);padding:12px;border-radius:8px;margin-top:10px}
.switch{position:relative;display:inline-block;width:50px;height:24px}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background-color:#4a5568;transition:.4s;border-radius:34px}
.slider:before{position:absolute;content:"";height:16px;width:16px;left:4px;bottom:4px;background-color:white;transition:.4s;border-radius:50%}
input:checked+.slider{background-color:#4361ee}
input:checked+.slider:before{transform:translateX(26px)}
.progress{height:10px;background:#2d3748;border-radius:10px;overflow:hidden;margin-top:15px}
.bar{height:100%;width:0%;background:#4cc9f0;transition:width 0.3s}
.status-area{text-align:center;margin-top:10px;font-size:14px;color:#a0aec0}
img{width:100%;border-radius:8px;margin-top:15px;display:none;border:2px solid rgba(255,255,255,0.1)}
</style>
</head>
<body>

<div class="box">
    <h2>Nokia Cloud ☁️</h2>
    <input id="url" placeholder="הדבק קישור (YouTube, TikTok...)">
    
    <select id="mode">
        <option value="360">🎬 איכות רגילה (360p)</option>
        <option value="720">🎬 איכות גבוהה (720p)</option>
        <option value="mp3">🎵 MP3 (אודיו)</option>
    </select>

    <div class="switch-container">
        <span>📱 מצב נוקיה 235 (240p)</span>
        <label class="switch">
            <input type="checkbox" id="nokiaSwitch" checked>
            <span class="slider"></span>
        </label>
    </div>

    <button onclick="start()" id="btn">התחל עיבוד</button>

    <img id="thumb">
    <div id="title" style="text-align:center;margin:10px 0;font-size:0.9em"></div>

    <div class="progress"><div class="bar" id="bar"></div></div>
    <div class="status-area">
        <span id="percent">0%</span> • <span id="status">מוכן</span>
    </div>
</div>

<script>
let id=null;
function start(){
    const btn = document.getElementById('btn');
    btn.disabled = true;
    document.getElementById('status').innerText = "מתחיל...";
    
    fetch('/start', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
            url: url.value, 
            mode: mode.value, 
            nokia: document.getElementById('nokiaSwitch').checked
        })
    }).then(r=>r.json()).then(d=>{
        if(d.error) { throw d.error }
        id = d.id;
        if(d.title) document.getElementById('title').innerText = d.title.substring(0,50) + "...";
        if(d.thumb) {
            let img = document.getElementById('thumb');
            img.src = d.thumb;
            img.style.display = 'block';
        }
        poll();
    }).catch(e => {
        alert("שגיאה: " + e);
        btn.disabled = false;
        document.getElementById('status').innerText = "נכשל";
    });
}

function poll(){
    fetch('/progress/'+id).then(r=>r.json()).then(d=>{
        document.getElementById('bar').style.width = d.percent + '%';
        document.getElementById('percent').innerText = d.percent + '%';
        
        if (d.mode === 'nokia' && d.percent >= 100 && !d.done) {
             document.getElementById('status').innerText = "⏳ השרת מכווץ לנוקיה...";
        } else if (d.done) {
             document.getElementById('status').innerText = "✅ הושלם!";
             window.location = '/file/'+id;
             document.getElementById('btn').disabled = false;
             document.getElementById('btn').innerText = "הורד עוד";
        } else {
             document.getElementById('status').innerText = "⬇️ מוריד... " + (d.speed || '');
        }

        if(!d.done) setTimeout(poll, 1500);
    })
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    uid = str(uuid.uuid4())
    is_nokia = data.get('nokia', False)
    tasks[uid] = {'percent': 0, 'done': False, 'mode': 'nokia' if is_nokia else 'std'}

    def hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','')
            try: tasks[uid]['percent'] = int(float(p))
            except: pass
            tasks[uid]['speed'] = d.get('_speed_str','')
        if d['status'] == 'finished': tasks[uid]['percent'] = 100

    ydl_opts = {
        'quiet': True, 
        'progress_hooks': [hook],
        'outtmpl': f"{uid}_src.%(ext)s",
        'format': 'best[height<=360]' if is_nokia else f"best[height<={data['mode']}]"
    }
    
    # Cookies support
    if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'

    if data['mode'] == 'mp3' and not is_nokia:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data['url'], download=True)
            dl_file = ydl.prepare_filename(info)
            if data['mode'] == 'mp3': dl_file = os.path.splitext(dl_file)[0] + '.mp3'

        if is_nokia and data['mode'] != 'mp3':
            final_file = f"{uid}_nokia.mp4"
            # הפקודה לנוקיה (רזולוציה נמוכה, פריימים נמוכים)
            subprocess.run([
                'ffmpeg', '-y', '-i', dl_file,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20', '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
                '-c:a', 'aac', '-ac', '1', '-b:a', '64k',
                final_file
            ], check=True)
            if os.path.exists(dl_file): os.remove(dl_file)
        else:
            final_file = dl_file

        tasks[uid]['file'] = final_file
        tasks[uid]['done'] = True
        return jsonify({'id': uid, 'title': info.get('title'), 'thumb': info.get('thumbnail')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<id>')
def check_progress(id): return jsonify(tasks.get(id, {}))

@app.route('/file/<id>')
def get_file(id):
    fpath = tasks[id].get('file')
    if not fpath or not os.path.exists(fpath): return "Expired", 404
    def generate():
        with open(fpath, "rb") as f: yield from f
        try: os.remove(fpath) # Clean up
        except: pass
    return Response(generate(), headers={"Content-Disposition": f"attachment; filename={fpath}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)