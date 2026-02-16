import threading # --- חובה להוסיף את זה בשביל לעבוד במקביל ---
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time

# --- FFmpeg Configuration for Render/Local ---
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

app = Flask(__name__)
tasks = {}

# HTML נשאר זהה למה ששלחת - הוא מעוצב יפה ותקין
HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="e_GuRsqVZunYgcIVNlkpDhD2I3l31jJ8AwjEVRxvqi0" />
<title>Nokia Cloud Converter</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* עיצוב כללי */
body { margin:0; min-height:100vh; display:flex; justify-content:center; align-items:center; 
       background:radial-gradient(circle at top,#1a1a2e,#16213e); font-family:'Segoe UI',Arial,sans-serif; color:white; }
.box { width:90%; max-width:450px; padding:25px; border-radius:16px; 
       background:rgba(255,255,255,.05); backdrop-filter:blur(10px); 
       box-shadow:0 8px 32px rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); }
h2 { text-align:center; margin-top:0; color:#4cc9f0; }
input, select, button { width:100%; padding:14px; margin:8px 0; border:none; 
                        border-radius:8px; font-size:16px; box-sizing:border-box; }
input, select { background:rgba(255,255,255,0.1); color:white; outline:none; }
select option { background-color: #16213e; color: white; }
button { background:linear-gradient(45deg,#4cc9f0,#4361ee); color:white; 
         font-weight:bold; cursor:pointer; transition:0.3s; }
button:disabled { opacity:0.6; cursor:not-allowed; }
.switch-container { display:flex; align-items:center; justify-content:space-between; 
                    background:rgba(255,255,255,0.05); padding:12px; border-radius:8px; margin-top:10px; }
.switch { position:relative; display:inline-block; width:50px; height:24px; }
.switch input { opacity:0; width:0; height:0; }
.slider { position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; 
          background-color:#4a5568; transition:.4s; border-radius:34px; }
.slider:before { position:absolute; content:""; height:16px; width:16px; left:4px; bottom:4px; 
                 background-color:white; transition:.4s; border-radius:50%; }
input:checked+.slider { background-color:#4361ee; }
input:checked+.slider:before { transform:translateX(26px); }
.progress { height:10px; background:#2d3748; border-radius:10px; overflow:hidden; margin-top:15px; }
.bar { height:100%; width:0%; background:#4cc9f0; transition:width 0.3s; }
.status-area { text-align:center; margin-top:10px; font-size:14px; color:#a0aec0; }
img { width:100%; border-radius:8px; margin-top:15px; display:none; border:2px solid rgba(255,255,255,0.1); }
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
    <div class="status-area"><span id="percent">0%</span> • <span id="status">מוכן</span></div>
</div>
<script>
let id=null;
function start(){
    const btn = document.getElementById('btn');
    const url = document.getElementById('url').value;
    const mode = document.getElementById('mode').value;
    const nokia = document.getElementById('nokiaSwitch').checked;

    if(!url){ alert("נא להדביק קישור"); return; }
    
    // איפוס ממשק
    btn.disabled = true;
    document.getElementById('thumb').style.display = 'none';
    document.getElementById('title').innerText = '';
    document.getElementById('status').innerText = "מתחבר לשרת...";
    document.getElementById('bar').style.width = '0%';
    document.getElementById('percent').innerText = '0%';
    
    fetch('/start', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ url: url, mode: mode, nokia: nokia })
    }).then(r=>r.json()).then(d=>{
        if(d.error) { throw d.error }
        id = d.id;
        // מיד מתחילים לתשאל
        poll();
    }).catch(e => {
        alert("שגיאה: " + e);
        btn.disabled = false;
        document.getElementById('status').innerText = "נכשל";
    });
}

function poll(){
    if(!id) return;
    fetch('/progress/'+id).then(r=>r.json()).then(d=>{
        document.getElementById('bar').style.width = d.percent + '%';
        document.getElementById('percent').innerText = d.percent + '%';
        
        // עדכון תמונה וכותרת ברגע שהם זמינים בשרת
        if(d.title && document.getElementById('title').innerText === '') {
             document.getElementById('title').innerText = d.title.substring(0,60) + "...";
        }
        if(d.thumb && document.getElementById('thumb').style.display === 'none') {
             document.getElementById('thumb').src = d.thumb;
             document.getElementById('thumb').style.display = 'block';
        }

        if (d.mode === 'nokia' && d.percent >= 100 && !d.done) {
             document.getElementById('status').innerText = "⏳ מבצע המרה לנוקיה...";
        } else if (d.done) {
             document.getElementById('status').innerText = "✅ הושלם!";
             window.location = '/file/'+id; // הורדה אוטומטית
             document.getElementById('btn').disabled = false;
             document.getElementById('btn').innerText = "הורד עוד";
        } else {
             document.getElementById('status').innerText = "⬇️ מוריד... " + (d.speed || '');
        }

        if(!d.done && !d.error) setTimeout(poll, 1500);
        if(d.error) {
             alert("שגיאה בעיבוד: " + d.error);
             document.getElementById('status').innerText = "שגיאה";
             document.getElementById('btn').disabled = false;
        }
    })
}
</script>
</body>
</html>
"""

def processing_thread(uid, url, mode_val, is_nokia):
    """זוהי הפונקציה שתרוץ ברקע"""
    try:
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            # אם מצב נוקיה, אין טעם להוריד איכות גבוהה, נחסוך זמן
            'format': 'best[height<=360]' if (is_nokia or mode_val=='360') else f"best[height<={mode_val}]"
        }

        if mode_val == 'mp3' and not is_nokia:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

        # Cookies check
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        def hook(d):
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('%','')
                try: 
                    tasks[uid]['percent'] = int(float(p))
                except: pass
                tasks[uid]['speed'] = d.get('_speed_str','')
            if d['status'] == 'finished':
                tasks[uid]['percent'] = 100

        ydl_opts['progress_hooks'] = [hook]

        # 1. חילוץ מידע
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            tasks[uid]['title'] = info.get('title')
            tasks[uid]['thumb'] = info.get('thumbnail')
            
            # 2. הורדה בפועל
            ydl.download([url])
            
            # מציאת שם הקובץ שהורד
            dl_file = ydl.prepare_filename(info)
            # בגלל באגים ב-ydl, לפעמים הסיומת משתנה לאחר המרה (כמו mkv->mp4 או mp4->mp3)
            # לכן נמצא את הקובץ עם השם שהתחיל ב-uid
            base_name = dl_file.rsplit('.', 1)[0]
            # ננסה לנחש אם הסיומת השתנתה (במקרה של mp3)
            if mode_val == 'mp3':
                possible_mp3 = base_name + '.mp3'
                if os.path.exists(possible_mp3): dl_file = possible_mp3
            elif not os.path.exists(dl_file):
                 # במקרה ש-mkv מוזג ל-mp4 וכו'
                 for f in os.listdir('.'):
                     if f.startswith(uid + "_src"):
                         dl_file = f
                         break

        # 3. המרת נוקיה (FFmpeg)
        if is_nokia and mode_val != 'mp3':
            final_file = f"{uid}_nokia.mp4"
            # הגדרות אופטימליות לנוקיה: רזולוציה נמוכה, אודיו מונו, ביטרייט נמוך
            cmd = [
                'ffmpeg', '-y', '-i', dl_file,
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20', 
                '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0', '-crf', '28',
                '-c:a', 'aac', '-ac', '1', '-b:a', '64k', '-ar', '44100',
                final_file
            ]
            subprocess.run(cmd, check=True)
            
            # מחיקת קובץ המקור
            if os.path.exists(dl_file): os.remove(dl_file)
        else:
            final_file = dl_file

        tasks[uid]['file'] = final_file
        tasks[uid]['done'] = True

    except Exception as e:
        print(f"Error processing {uid}: {e}")
        tasks[uid]['error'] = str(e)


@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    uid = str(uuid.uuid4())
    is_nokia = data.get('nokia', False)
    mode = data.get('mode', '360')
    
    # אתחול הנתונים במערך הגלובלי
    tasks[uid] = {
        'percent': 0, 
        'done': False, 
        'mode': 'nokia' if is_nokia else 'std',
        'title': '',
        'thumb': ''
    }

    # הרצת התהליך ב-Thread נפרד כדי לא לתקוע את השרת
    thread = threading.Thread(target=processing_thread, args=(uid, data['url'], mode, is_nokia))
    thread.start()

    # מחזירים תשובה מיידית ללקוח כדי שהפרוגרס-בר יתחיל לרוץ
    return jsonify({'id': uid})

@app.route('/progress/<id>')
def check_progress(id):
    return jsonify(tasks.get(id, {}))

@app.route('/file/<id>')
def get_file(id):
    task = tasks.get(id)
    if not task: return "Not found", 404
    fpath = task.get('file')
    
    if not fpath or not os.path.exists(fpath): return "File expired or Error", 404
    
    def generate():
        with open(fpath, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk: break
                yield chunk
        # נקיון בסוף ההורדה
        try: os.remove(fpath) 
        except: pass
        tasks.pop(id, None) # מנקה מהזיכרון

    # תיקון קטן לשמות הקבצים בעת ההורדה
    download_name = "nokia_video.mp4" if task['mode'] == 'nokia' else os.path.basename(fpath)
    
    return Response(generate(), headers={"Content-Disposition": f"attachment; filename={download_name}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
