#!/usr/bin/env bash
# יוצאים מיד אם פקודה נכשלת
set -o errexit

echo "🔹 Installing Python requirements..."
pip install -r requirements.txt

echo "🔹 Creating bin directory..."
mkdir -p bin

echo "🔹 Downloading FFmpeg static build..."
# מורידים קודם לקובץ כדי לוודא שההורדה הצליחה
curl -L -o ffmpeg.tar.xz https://github.com/eugeneware/ffmpeg-static/releases/latest/download/linux-x64.tar.gz

echo "🔹 Extracting FFmpeg..."
# חילוץ עדין יותר (משתמש ב-gz מהמקור היציב יותר של גיטהאב)
tar -xvz -f ffmpeg.tar.gz -C bin

# אם התיקייה שחולצה לא נקראת 'ffmpeg' (תלוי בארכיון), מזיזים את הבינארי לתיקייה הנכונה
# בקובץ הזה בדרך כלל הבינארי נמצא ישר
if [ -f bin/ffmpeg ]; then
    echo "✅ FFmpeg binary found directly."
else
    # חיפוש והזזה במידה וזה בתיקיית משנה
    find bin -name "ffmpeg" -type f -exec mv {} bin/ \;
fi

# נותנים הרשאות ריצה ליתר ביטחון
chmod +x bin/ffmpeg

echo "🔹 Cleaning up..."
rm ffmpeg.tar.gz

echo "✅ Build script finished successfully!"
