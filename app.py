from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form.get('url')
    
    if not video_url:
        return "אנא הכנס קישור תקין", 400

    unique_id = str(uuid.uuid4())
    temp_filename = f"video_{unique_id}"
    
    # --- השינוי הגדול כאן ---
    ydl_opts = {
        'format': 'best',
        'outtmpl': f"{temp_filename}.%(ext)s",
        'noplaylist': True,
        'quiet': True,
        # ביטול בדיקת תעודות אבטחה (לפעמים עוזר לעקוף חסימות)
        'nocheckcertificate': True,
        # זיוף דפדפן: אנחנו אומרים ליוטיוב שאנחנו כרום רגיל בווינדוס 10
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        # מנסה לדמות בקשה שמגיעה מלקוחות ניידים כדי להימנע מדרישת התחברות
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls']
            }
        }
    }
    # -----------------------

    try:
        final_filename = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            final_filename = ydl.prepare_filename(info_dict)

        def generate_file():
            with open(final_filename, 'rb') as f:
                yield from f
            os.remove(final_filename)

        download_name = f"{info_dict.get('title', 'video')}.{info_dict.get('ext', 'mp4')}"

        from flask import Response
        return Response(
            generate_file(),
            mimetype="application/octet-stream",
            headers={"Content-Disposition": f"attachment;filename={download_name}"}
        )

    except Exception as e:
        if final_filename and os.path.exists(final_filename):
            os.remove(final_filename)
        # מדפיס שגיאה ברורה יותר
        return f"<h1>שגיאה בהורדה</h1><p>נראה שיוטיוב חסמו את הכתובת של השרת הזה.</p><p>השגיאה המקורית: {str(e)}</p>"

if __name__ == '__main__':
    app.run(debug=True)
