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

    # יצירת שם קובץ זמני ייחודי למניעת התנגשויות בין משתמשים
    unique_id = str(uuid.uuid4())
    temp_filename = f"video_{unique_id}"
    
    ydl_opts = {
        'format': 'best', # איכות מיטבית (לרוב MP4 עם סאונד)
        'outtmpl': f"{temp_filename}.%(ext)s", # שמירה זמנית
        'noplaylist': True,
        'quiet': True 
    }

    try:
        final_filename = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # שלב א: משיכת מידע והורדה לשרת של רנדר
            info_dict = ydl.extract_info(video_url, download=True)
            # קבלת שם הקובץ האמיתי שנוצר (עם הסיומת הנכונה, למשל .mp4)
            final_filename = ydl.prepare_filename(info_dict)

        # פונקציה למחיקת הקובץ מיד לאחר שהדפדפן מסיים להוריד אותו
        def generate_file():
            with open(final_filename, 'rb') as f:
                yield from f
            # מחיקת הקובץ מהשרת
            os.remove(final_filename)

        # כותרת ההורדה בדפדפן (שם הקובץ המקורי של הסרטון)
        download_name = f"{info_dict.get('title', 'video')}.{info_dict.get('ext', 'mp4')}"

        # שליחת הקובץ בחזרה למשתמש
        from flask import Response
        return Response(
            generate_file(),
            mimetype="application/octet-stream",
            headers={"Content-Disposition": f"attachment;filename={download_name}"}
        )

    except Exception as e:
        # ניקוי במקרה של שגיאה (אם הקובץ נוצר)
        if final_filename and os.path.exists(final_filename):
            os.remove(final_filename)
        return f"<h1>שגיאה בהורדה</h1><p>{str(e)}</p><br><a href='/'>נסה שוב</a>"

if __name__ == '__main__':
    # הרצה מקומית בלבד
    app.run(debug=True)