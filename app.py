from flask import Flask, render_template_string, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# עיצוב הדף (HTML בתוך הקוד לנוחות)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מוריד עם Cookies</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background: #222; color: white; }
        input { padding: 10px; width: 300px; border-radius: 5px; }
        button { padding: 10px 20px; background: red; color: white; border: none; cursor: pointer; border-radius: 5px; font-weight: bold; }
        .spinner { display: none; margin: 20px auto; border: 4px solid #f3f3f3; border-top: 4px solid red; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>🚀 מוריד סרטונים (Render + Cookies)</h1>
    <form action="/download" method="post" onsubmit="document.getElementById('spin').style.display='block'">
        <input type="text" name="url" placeholder="הדבק קישור יוטיוב..." required>
        <button type="submit">הורד</button>
    </form>
    <div id="spin" class="spinner"></div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form.get('url')
    if not video_url: return "חסר קישור", 400

    unique_id = str(uuid.uuid4())
    temp_filename = f"video_{unique_id}"
    
    # בדיקה שקובץ הקוקיז קיים בתיקייה
    if not os.path.exists("cookies.txt"):
        return "שגיאה קריטית: קובץ cookies.txt לא נמצא בשרת! העלה אותו לגיטהאב."

    ydl_opts = {
        'format': 'best',
        'outtmpl': f"{temp_filename}.%(ext)s",
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies.txt'  # <--- הנה הקסם שעוקף את החסימה
    }

    try:
        final_filename = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            final_filename = ydl.prepare_filename(info)

        def generate():
            with open(final_filename, 'rb') as f:
                yield from f
            os.remove(final_filename)

        download_name = f"{info.get('title', 'video')}.{info.get('ext', 'mp4')}"
        
        # טיפול בשמות בעברית להורדה תקינה
        try:
            download_name.encode('latin-1')
        except UnicodeEncodeError:
            download_name = 'video_download.mp4'

        from flask import Response
        return Response(generate(), mimetype="application/octet-stream", 
                       headers={"Content-Disposition": f"attachment;filename={download_name}"})

    except Exception as e:
        if final_filename and os.path.exists(final_filename): os.remove(final_filename)
        return f"<h1>שגיאה</h1><p>{e}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
