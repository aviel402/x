#!/usr/bin/env bash
# יוצא מיד אם יש שגיאה
set -e 

echo "Installing Python requirements..."
pip install -r requirements.txt

echo "Downloading and extracting static FFmpeg..."
# יצירת תיקייה לכלים
mkdir -p bin
# הורדת תוכנת ההמרה מכיוון שברנדר אין גישת אדמין (sudo)
wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz --strip-components=1 -C bin/

# נותן הרשאות הרצה לקובץ ההמרה
chmod +x ./bin/ffmpeg

echo "Build setup finished!"

echo "start!"
echo "👌👌👌"

python3 app.py
