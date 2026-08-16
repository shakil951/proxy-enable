import re
import urllib.parse
import requests

# ব্যাকআপ সহ সোর্স তালিকা
SOURCE_URLS = [
    "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/refs/heads/main/toffee_playlist.m3u",
    "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/main/toffee_playlist.m3u",
    "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update-Playlist/main/toffee_playlist.m3u"
]

PROXY_BASE = "https://toffee-proxy.usergamil15.workers.dev/"
SECRET_KEY = "FS_LIVE_TV_SECRET_2026"
OUTPUT_FILE = "playlist.m3u"

def fetch_source_text():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for url in SOURCE_URLS:
        try:
            print(f"Checking source: {url}")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200 and len(res.text) > 100:
                print(" Successfully loaded source file.")
                return res.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
    return None

def extract_master_cookie(content):
    # পুরো ফাইলের যেকোনো জায়গা থেকে URLPrefix ও Signature যুক্ত কুকি খোঁজা
    cookie_match = re.search(r'(URLPrefix%3D[^\s"\'\n\r&]+|URLPrefix=[^\s"\'\n\r&]+)', content)
    if cookie_match:
        raw_cookie = cookie_match.group(1)
        # আন-কোড করে ক্লিন করা
        clean_cookie = urllib.parse.unquote(raw_cookie)
        if not clean_cookie.startswith("Edge-Cache-Cookie="):
            clean_cookie = f"Edge-Cache-Cookie={clean_cookie}"
        return urllib.parse.quote(clean_cookie, safe="")
    return ""

def generate_proxy_playlist():
    content = fetch_source_text()
    if not content:
        print(" Error: Could not fetch source playlist from any URL.")
        return

    # ১. গ্লোবাল কুকি এক্সট্রাক্ট
    encoded_cookie = extract_master_cookie(content)
    print(f"Extracted Cookie Status: {'FOUND' if encoded_cookie else 'NOT FOUND'}")

    lines = content.replace("\r", "").split("\n")
    channels = []
    current_title = ""

    # ২. চ্যানেল ও লিংক পার্সিং
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue

        if trimmed.startswith("#EXTINF:"):
            parts = trimmed.split(",", 1)
            current_title = parts[1].strip() if len(parts) > 1 else "Toffee Channel"
        elif not trimmed.startswith("#") and ("http://" in trimmed or "https://" in trimmed):
            raw_url = trimmed
            
            # লিঙ্ক থেকে আগের অতিরিক্ত প্যারামিটার রিমুভ
            if "cookie=" in raw_url:
                raw_url = raw_url.split("cookie=")[0]
            if "url=" in raw_url and "workers.dev" in raw_url:
                # যদি অলরেডি প্রক্সি ফরম্যাটে থাকে
                extracted = re.search(r'url=([^&]+)', raw_url)
                if extracted:
                    raw_url = urllib.parse.unquote(extracted.group(1))

            raw_url = re.sub(r'[?&]$', '', raw_url)
            
            # শুধুমাত্র টুফি প্লেলিস্ট/লাইভ স্ট্রিম ফিল্টার
            if "bldcmprod-cdn" in raw_url or "toffeelive" in raw_url or ".m3u8" in raw_url:
                encoded_stream_url = urllib.parse.quote(raw_url, safe="")

                # টার্গেট প্রক্সি লিংক তৈরি
                proxied_url = (
                    f"{PROXY_BASE}?url={encoded_stream_url}"
                    f"&cookie={encoded_cookie}"
                    f"&secret_key={SECRET_KEY}"
                )

                channels.append({
                    "title": current_title or f"Toffee Channel {len(channels) + 1}",
                    "url": proxied_url
                })

            current_title = ""

    print(f"Total valid channels found: {len(channels)}")

    if not channels:
        print(" No channels parsed. Writing fallback.")
        return

    # ৩. M3U ফাইল সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for ch in channels:
            f.write(f'#EXTINF:-1 group-title="Toffee Live", {ch["title"]}\n')
            f.write(f'{ch["url"]}\n\n')

    print(f" Successfully generated {OUTPUT_FILE} with {len(channels)} channels!")

if __name__ == "__main__":
    generate_proxy_playlist()
