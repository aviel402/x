import os
import subprocess
import requests
from flask import Flask

app = Flask(__name__)

# רשימת הקישורים לסרטים (תחליף לאילו שלך)
DS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    # "https://example.com/another-video.mp4"
]

def download_and_convert_videos():
    # יוצר תיקייה שאליה יכנסו הסרטים המומרים
    os.makedirs('converted_movies', exist_ok=True)
    
    # מיקום קובץ ההמרה שהותקן דרך build.sh
    ffmpeg_path = './bin/ffmpeg'

    for index, url in enumerate(DS):
        # הגדרת שמות הקבצים הזמניים והמומרים
        temp_video = f"temp_video_{index}.mp4"
        final_video = f"converted_movies/movie_{index}.avi"
        
        # בודק אם הסרט כבר הומר בעבר כדי לחסוך זמן
        if os.path.exists(final_video):
            print(f"Movie {index} already converted.")
            continue

        try:
            # 1. מוריד את הסרט אל קובץ זמני
            print(f"Downloading movie {index}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(temp_video, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            
            # 2. ממיר אותו לפורמט AVI ומשנה את הרזולוציה ל 320x240
            print(f"Converting movie {index} to AVI 320x240...")
            command = [
                ffmpeg_path,
                '-i', temp_video,       # קובץ קלט
                '-vf', 'scale=320:240', # שינוי רזולוציה
                '-c:v', 'mpeg4',        # קודק וידאו שנתמך טוב ב-avi
                '-c:a', 'libmp3lame',   # קודק אודיו (mp3)
                '-y',                   # דרוס קובץ אם קיים
                final_video             # קובץ פלט
            ]
            
            # הרצת הפקודה מול שורת הפקודה
            subprocess.run(command, check=True)
            print(f"Movie {index} converted successfully!")

        except Exception as e:
            print(f"Error processing movie {index}: {e}")
        
        finally:
            # מחיקת קובץ המקור כדי לחסוך מקום בשרת של Render
            if os.path.exists(temp_video):
                os.remove(temp_video)

# פקודה זו מפעילה את הורדת והמרת הסרטים ברגע שהשרת עולה
print("Starting download and conversion process...")
download_and_convert_videos()

@app.route('/')
def index():
    files = os.listdir('converted_movies') if os.path.exists('converted_movies') else []
    return f"<h1>The Server is Running</h1><p>Converted {len(files)} files successfully.</p>"

if __name__ == '__main__':
    # הרצת השרת עבור רנדר (שמחייב קישור לפורט 10000 או משתנה סביבה)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
