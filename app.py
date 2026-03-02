import os
import subprocess
import requests
import threading
from flask import Flask, send_from_directory

app = Flask(__name__)

# רשימת הקישורים לסרטים שלכם (משתנה ה-DS המבוקש)
DS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    # הוסף כאן עוד קישורים ישירים לסרטים...
]

def download_and_convert_videos():
    # יוצר תיקייה לסרטים המומרים
    CONVERTED_DIR = 'converted_movies'
    os.makedirs(CONVERTED_DIR, exist_ok=True)
    
    # מיקום תוכנת ההמרה שהורדה ב-build.sh
    ffmpeg_path = './bin/ffmpeg'

    for index, url in enumerate(DS):
        # קביעת שמות קבצים דינמיים לפי הסדר ברשימה
        base_name = f"movie_{index + 1}"
        temp_video = f"{base_name}_temp.mp4"
        final_video = f"{CONVERTED_DIR}/{base_name}.avi"
        
        # דילוג אם הסרט הספציפי כבר קיים (מונע עבודה כפולה)
        if os.path.exists(final_video):
            print(f"{final_video} already exists. Skipping.")
            continue

        try:
            # 1. מוריד את קובץ המקור מהאינטרנט
            print(f"[{base_name}] Downloading from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(temp_video, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            
            # 2. הרצת הפקודה שממירה לגודל 320x240 בסיומת AVI
            print(f"[{base_name}] Converting to AVI (320x240)...")
            command = [
                ffmpeg_path,
                '-i', temp_video,
                '-vf', 'scale=320:240',
                '-c:v', 'mpeg4',
                '-c:a', 'libmp3lame',
                '-y',
                final_video
            ]
            subprocess.run(command, check=True)
            print(f"[{base_name}] Done converting! Ready for download.")

        except Exception as e:
            print(f"Error processing {url}: {e}")
        
        finally:
            # מחיקת קובץ הזבל כדי לפנות מקום בכונן ברנדר
            if os.path.exists(temp_video):
                os.remove(temp_video)

# הפעלת תהליך ההורדה וההמרה בתהליך רקע (Background Thread)
# ככה השרת שלנו עולה מהר ו-Render לא מכבה אותנו על איטיות!
def run_in_background():
    download_and_convert_videos()

thread = threading.Thread(target=run_in_background)
thread.start()


# -------- ראוטים של עמוד האינטרנט עצמו --------

# 1. דף הבית שיציג לנו את הסרטים הקיימים עם כפתורי הורדה
@app.route('/')
def index():
    CONVERTED_DIR = 'converted_movies'
    # מקבל רשימה של הקבצים שבתיקייה
    files = os.listdir(CONVERTED_DIR) if os.path.exists(CONVERTED_DIR) else []
    
    # תצוגה פשוטה ובסיסית של עמוד HTML
    html_content = '<html dir="rtl"><body style="font-family: Arial;">'
    html_content += "<h2>🎬 מאגר סרטים להורדה (מצב המרה: פעיל ברקע)</h2>"
    
    avi_files = [f for f in files if f.endswith('.avi')]
    
    if not avi_files:
        html_content += "<p>המערכת מתחילה כעת המרה... נסו לרענן את העמוד בעוד מספר דקות.</p>"
    else:
        html_content += "<ul>"
        for f in avi_files:
            # מייצר לינק אקטיבי עבור כל סרט שישלח להורדה
            html_content += f'<li style="margin:10px;"><a href="/download/{f}" style="padding: 5px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">הורד את: {f}</a></li>'
        html_content += "</ul>"
        html_content += "<p><em>שימו לב: סרטים נוספים עשויים להתווסף אם התהליך עוד רץ - תרעננו!</em></p>"
        
    html_content += '</body></html>'
    return html_content

# 2. הראוט שאחראי בפועל להוריד את הקובץ אל המחשב שלכם ברגע שלחצתם על הכפתור
@app.route('/download/<filename>')
def download_file(filename):
    # הפקודה המיוחדת בפייתון להוציא קובץ מהשרת אליך הביתה - כאטרצ'מנט (כקובץ מצורף שמקפיץ הורדה)
    return send_from_directory('converted_movies', filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
