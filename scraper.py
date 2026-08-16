import re
import urllib.parse
import requests

SOURCE_URLS = [
    "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/refs/heads/main/toffee_playlist.m3u",
    "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/main/toffee_playlist.m3u"
]

PROXY_BASE = "https://toffee-proxy.usergamil15.workers.dev/"
SECRET_KEY = "FS_LIVE_TV_SECRET_2026"
OUTPUT_FILE = "playlist.m3u"

def get_source():
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in SOURCE_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200 and len(r.text) > 100:
                return r.text
        except Exception:
            pass
    return None

def clean_cookie(text):
    match = re.search(r'(URLPrefix[^"\s\n\r&]+)', text)
    if match:
        c = match.group(1)
        # যদি আগে থেকে এনকোড থাকে ডিকোড করে প্লেইন করা
        while "%" in c:
            decoded = urllib.parse.unquote(c)
            if decoded == c:
                break
            c = decoded
        if not c.startswith("Edge-Cache-Cookie="):
            c = "Edge-Cache-Cookie=" + c
        return urllib.parse.quote(c, safe="")
    return ""

def build_playlist():
    content = get_source()
    if not content:
        print("Source fetch failed")
        return

    cookie_encoded = clean_cookie(content)
    lines = content.replace("\r", "").split("\n")
    
    out_lines = ["#EXTM3U\n"]
    current_ext = ""

    for line in lines:
        l = line.strip()
        if not l:
            continue

        if l.startswith("#EXTINF:"):
            # অপ্রয়োজনীয় ডাবল স্পেস ক্লিন করা
            current_ext = l
        elif not l.startswith("#") and ("http://" in l or "https://" in l):
            raw_stream = l
            if "cookie=" in raw_stream:
                raw_stream = raw_stream.split("cookie=")[0]
            if "url=" in raw_stream:
                m = re.search(r'url=([^&]+)', raw_stream)
                if m:
                    raw_stream = urllib.parse.unquote(m.group(1))
            
            raw_stream = re.sub(r'[?&]$', '', raw_stream)
            raw_stream = urllib.parse.unquote(raw_stream)

            # পারফেক্ট সিঙ্গেল এনকোডিং
            encoded_url = urllib.parse.quote(raw_stream, safe="")
            
            final_proxy_url = (
                f"{PROXY_BASE}?url={encoded_url}"
                f"&cookie={cookie_encoded}"
                f"&secret_key={SECRET_KEY}"
            )

            # এক্সটি ইনফো ঠিক রাখা
            ext_line = current_ext if current_ext else '#EXTINF:-1 group-title="Toffee Live",Toffee Live'
            out_lines.append(f"{ext_line}\n{final_proxy_url}\n")
            current_ext = ""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines("\n".join(out_lines))

    print(f"Generated clean playlist for Android apps.")

if __name__ == "__main__":
    build_playlist()
