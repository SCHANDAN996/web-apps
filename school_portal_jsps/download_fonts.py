import urllib.request
import os

files = [
    "mfglabsiconset-webfont.eot", "mfglabsiconset-webfont.svg", 
    "mfglabsiconset-webfont.woff", "mfglabsiconset-webfont.ttf",
    "Simple-Line-Icons.eot", "Simple-Line-Icons.ttf", 
    "Simple-Line-Icons.woff2", "Simple-Line-Icons.woff", "Simple-Line-Icons.svg"
]

os.makedirs("static/font/", exist_ok=True)

for f in files:
    url = f"https://jspschandauli.com/font/{f}"
    dest = f"static/font/{f}"
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"Saved to {dest}")
    except Exception as e:
        print(f"Failed to download {f}: {e}")
