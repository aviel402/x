import threading
from flask import Flask, request, Response, jsonify, render_template_string
import yt_dlp, uuid, os, subprocess, time
from urllib.parse import quote

# --- FFmpeg Setup ---
# וידוא ש-ffmpeg נמצא בנתיב הריצה
if os.path.exists("bin"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

app = Flask(__name__)

# זיכרון גלובלי למשימות
tasks = {}

# --- מערכת ניקוי אוטומטית (Garbage Collection) ---
def cleanup_loop():
    while True:
        try:
            current_time = time.time()
            to_delete = []
            
            # בדיקת משימות שפג תוקפן
            for uid, task in list(tasks.items()):
                # מוחק אחרי 20 דקות
                if current_time - task.get('timestamp', 0) > 1200:  
                    file_path = task.get('file')
                    if file_path and os.path.exists(file_path):
                        try: os.remove(file_path)
                        except: pass
                    # מחיקת קבצים זמניים (שאריות)
                    for f in os.listdir('.'):
                        if f.startswith(uid):
                            try: os.remove(f)
                            except: pass
                    to_delete.append(uid)
            
            for uid in to_delete:
                del tasks[uid]
                print(f"[CLEANUP] Removed expired task {uid}")
                
        except Exception as e:
            print(f"Cleanup Error: {e}")
        
        time.sleep(60) # בודק כל דקה

cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
cleanup_thread.start()

HTML = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="e_GuRsqVZunYgcIVNlkpDhD2I3l31jJ8AwjEVRxvqi0" />
<title>Nokia Converter - AVI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* עיצוב רטרו-מודרני */
body { margin:0; min-height:100vh; display:flex; justify-content:center; align-items:center; 
       background:radial-gradient(circle at center,#1e3c72,#2a5298); 
       font-family:'Segoe UI',sans-serif; color:#fff; overflow-y: auto; padding: 20px;}
.box { width:100%; max-width:400px; padding:25px; border-radius:15px; 
       background:rgba(0,0,0,0.4); backdrop-filter:blur(10px); 
       box-shadow:0 15px 35px rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.1); }
h2 { text-align:center; margin-bottom:20px; color:#4cc9f0; font-weight:700;}
input, select, button { width:100%; padding:14px; margin:8px 0; border:none; 
                        border-radius:8px; font-size:16px; box-sizing: border-box;}
input, select { background:rgba(255,255,255,0.1); color:#fff; outline:none;}
select option { background:#333; color:#fff; }
button { background:#4cc9f0; color:#000; font-weight:bold; cursor:pointer; transition:0.3s; }
button:hover { background:#48bfe3; transform: scale(1.02); }
button:disabled { background:#555; color:#999; cursor:not-allowed; transform:none; }

.switch-container { display:flex; align-items:center; justify-content:space-between; 
                    background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-top:10px; }
.switch { position:relative; display:inline-block; width:46px; height:24px; }
.switch input { opacity:0; width:0; height:0; }
.slider { position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; 
          background-color:#4a5568; transition:.4s; border-radius:34px; }
.slider:before { position:absolute; content:""; height:16px; width:16px; left:4px; bottom:4px; 
                 background-color:white; transition:.4s; border-radius:50%; }
input:checked+.slider { background-color:#4cc9f0; }
input:checked+.slider:before { transform:translateX(22px); }

.progress-area { margin-top:15px; display:none; }
.progress-bar { height:8px; background:#333; border-radius:5px; overflow:hidden; position:relative;}
.fill { height:100%; width:0%; background:#4cc9f0; transition:width 0.4s; }
.status-text { text-align:center; font-size:13px; color:#ccc; margin-top:8px;}
img { width:100%; border-radius:8px; margin-top:15px; display:none; border:2px solid rgba(255,255,255,0.1);}
</style>
</head>
<body>
<div class="box">
    <h2>Nokia Cloud ☁️</h2>
    <input id="url" placeholder="הדבק כאן קישור (YouTube, TikTok...)">
    <select id="mode">
        <option value="360">📺 רגיל (MP4)</option>
        <option value="mp3">🎧 אודיו בלבד (MP3)</option>
    </select>
    <div class="switch-container">
        <span>💾 מצב נוקיה (AVI 240p)</span>
        <label class="switch">
            <input type="checkbox" id="nokiaSwitch" checked>
            <span class="slider"></span>
        </label>
    </div>
    
    <button onclick="start()" id="btn">הורד</button>
    
    <div id="result" class="progress-area">
        <img id="thumb">
        <div id="title" style="text-align:center; font-size:14px; margin:10px 0;"></div>
        <div class="progress-bar"><div class="fill" id="bar"></div></div>
        <div class="status-text" id="status">ממתין...</div>
    </div>
</div>

<script>
let id = null;
let timer = null;

function start(){
    const url = document.getElementById('url').value;
    if(!url) return alert("חסר קישור");
    
    // UI Setup
    document.getElementById('btn').disabled = true;
    document.getElementById('btn').innerText = "אנא המתן...";
    document.getElementById('result').style.display = 'block';
    document.getElementById('thumb').style.display = 'none';
    document.getElementById('bar').style.width = '0%';
    document.getElementById('title').innerText = '';
    
    fetch('/start', {
        method:'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
            url: url,
            mode: document.getElementById('mode').value,
            nokia: document.getElementById('nokiaSwitch').checked
        })
    }).then(r=>r.json()).then(d=>{
        if(d.error) throw d.error;
        id = d.id;
        timer = setInterval(poll, 1000);
    }).catch(e=>{
        alert(e);
        location.reload();
    });
}

function poll(){
    fetch('/progress/'+id).then(r=>r.json()).then(d=>{
        if(d.error) {
            clearInterval(timer);
            alert("שגיאה: " + d.error);
            location.reload();
            return;
        }
        
        // עדכון UI
        document.getElementById('bar').style.width = d.percent + '%';
        if(d.title) document.getElementById('title').innerText = d.title;
        if(d.thumb && document.getElementById('thumb').style.display === 'none') {
             document.getElementById('thumb').src = d.thumb;
             document.getElementById('thumb').style.display = 'block';
        }

        let status = "מוריד... " + (d.percent||0) + "%";
        if(d.converting) status = "🔄 ממיר לפורמט נוקיה (AVI)...";
        if(d.done) status = "✅ הושלם!";
        document.getElementById('status').innerText = status;

        if(d.done){
            clearInterval(timer);
            document.getElementById('btn').innerText = "הורד קובץ";
            document.getElementById('btn').disabled = false;
            document.getElementById('btn').onclick = ()=> window.location='/file/'+id;
            window.location='/file/'+id; // Auto download
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
        
        # 1. הגדרות yt-dlp - תמיד מוריד הכי טוב עד 360p כדי לחסוך רוחב פס
        ydl_opts = {
            'quiet': True,
            'outtmpl': f"{uid}_src.%(ext)s",
            'format': 'best[height<=360]/best', 
            'nocheckcertificate': True
        }

        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        # רק אם ביקשו MP3 ספציפי וזה לא נוקיה
        if mode_val == 'mp3' and not is_nokia:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key':'FFmpegExtractAudio','preferredcodec':'mp3'}]

        def hook(d):
            if d['status'] == 'downloading':
                try:
                    p = float(d.get('_percent_str','0%').replace('%',''))
                    tasks[uid]['percent'] = int(p)
                except: pass
            if d['status'] == 'finished':
                tasks[uid]['percent'] = 95
                tasks[uid]['converting'] = True

        ydl_opts['progress_hooks'] = [hook]

        # ביצוע ההורדה
        info = None
        dl_filename = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            tasks[uid]['title'] = info.get('title','video')
            tasks[uid]['thumb'] = info.get('thumbnail')
            
            # זיהוי קובץ המקור
            for f in os.listdir('.'):
                if f.startswith(f"{uid}_src"):
                    dl_filename = f
                    break

        if not dl_filename: raise Exception("Download failed")

        # קביעת שם הקובץ הסופי
        safe_title = "".join([c for c in info.get('title','video') if c.isalnum() or c in ' .-_']).strip()
        
        # === טיפול מיוחד בנוקיה (AVI) ===
        if is_nokia and mode_val != 'mp3':
            final_path = f"{uid}_final.avi" # סיומת AVI חובה לנוקיה ישן
            final_display = f"{safe_title}.avi"
            
            cmd = [
                'ffmpeg', '-y', '-i', dl_filename,
                # רזולוציה קטנה עם שמירה על יחס
                '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2',
                '-r', '20',             # פריימים נמוכים (20FPS)
                '-c:v', 'mpeg4',        # קודק וידאו קלאסי (Xvid תואם)
                '-vtag', 'xvid',        # "משקר" לנגן שזה Xvid
                '-b:v', '300k',         # ביטרייט וידאו נמוך לקובץ קטן
                '-c:a', 'libmp3lame',   # קודק אודיו MP3
                '-ac', '1',             # אודיו מונו (ערוץ אחד - חוסך מקום)
                '-ar', '22050',         # איכות דגימה בינונית
                '-b:a', '48k',          # ביטרייט אודיו נמוך
                final_path
            ]
            subprocess.run(cmd, check=True)
            try: os.remove(dl_filename)
            except: pass
            
        elif mode_val == 'mp3':
            # אם ביקשו MP3, פשוט משנים את השם
            # (במידה ו-ydl המיר, הסיומת כבר תהיה mp3)
            ext = dl_filename.split('.')[-1]
            final_path = f"{uid}_final.{ext}"
            final_display = f"{safe_title}.{ext}"
            os.rename(dl_filename, final_path)
            
        else:
            # המרה רגילה ל-MP4 תקין לכל שאר המכשירים
            final_path = f"{uid}_final.mp4"
            final_display = f"{safe_title}.mp4"
            # ffmpeg מהיר להבטחת תאימות
            cmd = ['ffmpeg','-y','-i',dl_filename,'-c','copy','-movflags','+faststart',final_path]
            try:
                subprocess.run(cmd, check=True)
                os.remove(dl_filename)
            except:
                os.rename(dl_filename, final_path) # גיבוי אם ffmpeg נכשל בקופי

        tasks[uid]['file'] = final_path
        tasks[uid]['display_name'] = final_display
        tasks[uid]['percent'] = 100
        tasks[uid]['done'] = True
        tasks[uid]['converting'] = False

    except Exception as e:
        print(f"Error: {e}")
        tasks[uid]['error'] = str(e)
        try: # מחיקת שאריות במקרה שגיאה
            for f in os.listdir('.'):
                if f.startswith(uid): os.remove(f)
        except: pass

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/start', methods=['POST'])
def start_task():
    data = request.json
    uid = str(uuid.uuid4())
    tasks[uid] = {
        'percent':0, 'done':False, 'converting':False, 
        'timestamp': time.time(),
        'mode': 'nokia' if data.get('nokia') else data.get('mode')
    }
    threading.Thread(target=processing_thread, args=(uid, data['url'], data['mode'], data.get('nokia'))).start()
    return jsonify({'id': uid})

@app.route('/progress/<id>')
def get_progress(id):
    return jsonify(tasks.get(id, {'error':'Not found'}))

@app.route('/file/<id>')
def serve_file(id):
    task = tasks.get(id)
    if not task: return "Expired", 404
    fpath = task.get('file')
    if not fpath or not os.path.exists(fpath): return "Error", 404
    
    # שם הקובץ שיוצג להורדה
    dname = task.get('display_name', 'video.avi')
    try: encoded_name = quote(dname)
    except: encoded_name = "download"

    def generate():
        with open(fpath, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk: break
                yield chunk
    
    resp = Response(generate(), mimetype='application/octet-stream')
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_name}"
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
