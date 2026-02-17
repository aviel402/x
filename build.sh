#!/usr/bin/env bash
set -o errexit

# 1. התקנת ספריות פייתון
echo "🔹 Installing dependencies..."
pip install -r requirements.txt

# 2. יצירת תיקיות
echo "🔹 Preparing directories..."
mkdir -p bin
mkdir -p temp_ffmpeg  # תיקייה זמנית לחילוץ

# 3. הורדת FFmpeg
echo "🔹 Downloading FFmpeg..."
curl -L -o ffmpeg.tar.xz https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz

# 4. חילוץ לתיקייה זמנית (כדי לא ללכלך את bin)
echo "🔹 Extracting..."
tar -xJf ffmpeg.tar.xz -C temp_ffmpeg

# 5. ציד ומיקום מחדש: מוצאים את ffmpeg ו-ffprobe בכל תת-תיקייה ומעבירים ל-bin
echo "🔹 Locating binaries..."
find temp_ffmpeg -name "ffmpeg" -type f -exec mv -v {} bin/ \;
find temp_ffmpeg -name "ffprobe" -type f -exec mv -v {} bin/ \;

# 6. מתן הרשאות ריצה
chmod +x bin/ffmpeg
chmod +x bin/ffprobe

# 7. בדיקה וניקוי
if [ -f bin/ffmpeg ]; then
    echo "✅ FFmpeg installed successfully!"
    # מחיקת התיקייה הזמנית והקובץ הדחוס
    rm -rf temp_ffmpeg ffmpeg.tar.xz
else
    echo "❌ Error: ffmpeg binary not found even after search."
    ls -R temp_ffmpeg
    exit 1
fi
