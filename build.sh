#!/usr/bin/env bash
set -o errexit

# 1. התקנת ספריות פייתון
echo "🔹 Installing dependencies..."
pip install -r requirements.txt

# 2. יצירת תיקייה
echo "🔹 Creating bin directory..."
mkdir -p bin

# 3. הורדת FFmpeg ממקור יציב ומהיר (GitHub של yt-dlp)
echo "🔹 Downloading FFmpeg..."
curl -L -o ffmpeg.tar.xz https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz

# 4. בדיקה שההורדה באמת הצליחה (שהקובץ לא ריק)
filesize=$(stat -c%s ffmpeg.tar.xz)
if (( filesize < 1000000 )); then
    echo "❌ Error: Download failed (file too small). Exiting."
    exit 1
fi

# 5. חילוץ הקובץ (דגל J מיועד לקבצי xz)
echo "🔹 Extracting FFmpeg..."
tar -xJf ffmpeg.tar.xz -C bin --strip-components=1

# 6. בדיקה סופית ומתן הרשאות
if [ -f bin/ffmpeg ]; then
    chmod +x bin/ffmpeg
    echo "✅ FFmpeg installed successfully!"
else
    echo "❌ Error: ffmpeg binary not found in bin/"
    ls -R bin/
    exit 1
fi

# 7. ניקוי
rm ffmpeg.tar.xz
