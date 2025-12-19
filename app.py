from flask import Flask, render_template_string, request, Response
import yt_dlp
import os
import uuid
import json

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>🔥 Video Downloader Pro</title>
<style>
body {
    background: linear-gradient(135deg,#0f0f0f,#1a1a1a);
    color:white;
    font-family: Arial;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}
.card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    padding:30px;
    border-radius:20px;
    width:380px;
    box-shadow: 0 0 40px rgba(255,0,0,0.3);
}
h1 { margin-bottom:20px; }
input, select {
    width:100%;
    padding:12px;
    margin:10px 0;
    border-radius:10px;
    border:none;
}
button {
    width:100%;
    padding:14px;
    background:red;
    color:white;
    font-size:18px;
    border:none;
    border-radius:12px;
    cursor:pointer;
}
.progress-box {
    margin-top:20px;
    display:none;
}
.progress {
    height:18px;
    background:#333;
    border-radius:20px;
    overflow:hidden;
}
.bar {
    height:100%;
    width:0%;
    background: linear-gradient(90deg,red,orange);
    transition:0.3s;
}
.percent { margin-top:8px; }
</style>
</head>
<body>

<div class="card">
<h1>🚀 מוריד חכם</h1>

<input id="url" placeholder="הדבק קישור">
<select id="type">
  <option value="mp4">🎬 וידאו MP4</option>
  <option value="mp3">🎵 אודיו MP3</option>
</select>

<button onclick="start()">הורד</button>

<div class="progress-box" id="box">
  <div class="progress">
    <div class="bar" id="bar"></div>
  </div>
  <div class="percent" id="percent">0%</div>
</div>

</div>

<script>
function start(){
  document.getElementById('box').style.display='block'
  fetch('/download',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      url:document.getElementById('url').value,
      type:document.getElementById('type').value
    })
  }).then(r=>{
    const reader = r.body.getReader()
    let received = 0
    const total = +r.headers.get('Content-Length')
    return reader.read().then(function process({done,value}){
      if(done) return
      received += value.length
      let p = Math.floor(received/total*100)
      bar.style.width=p+'%'
      percent.innerText=p+'%'
      return reader.read().then(process)
    })
  })
}
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data['url']
    mode = data['type']

    uid = str(uuid.uuid4())
    out = f"file_{uid}"

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt'
    }

    if mode == 'mp3':
        ydl_opts.update({
            'format':'bestaudio',
            'outtmpl': out,
            'postprocessors':[{
                'key':'FFmpegExtractAudio',
                'preferredcodec':'mp3'
            }]
        })
    else:
        ydl_opts.update({
            'format':'best[height<=720]',
            'outtmpl': out + '.%(ext)s'
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    def stream():
        with open(filename,'rb') as f:
            yield from f
        os.remove(filename)

    return Response(stream(), headers={
        "Content-Disposition":"attachment"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
