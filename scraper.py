import re
import urllib.parse
import requests

# সোর্স যেখান থেকে ফ্রেশ কুকি ও চ্যানেল আসে
GITHUB_SOURCE_M3U = "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/refs/heads/main/toffee_playlist.m3u"

# আপনার টার্গেট প্রক্সি ফরম্যাট কনফিগারেশন
PROXY_BASE = "https://toffee-proxy.usergamil15.workers.dev/"
SECRET_KEY = "FS_LIVE_TV_SECRET_2026"
OUTPUT_FILE = "playlist.m3u"

def generate_proxy_playlist():
    print(f"Fetching source playlist from: {GITHUB_SOURCE_M3U}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        res = requests.get(GITHUB_SOURCE_M3U, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch source playlist. Status: {res.status_code}")
            return
    except Exception as e:
        print(f"Error fetching source: {e}")
        return

    content = res.text
    lines = content.replace("\r", "").split("\n")

    channels = []
    current_title = ""
    current_cookie = ""
    current_ua = "Toffee (Linux;Android 14)"

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue

        if trimmed.startswith("#EXTINF:"):
            # চ্যানেলের নাম এক্সট্রাক্ট করা (কমা দিয়ে ভাগ করে)
            parts = trimmed.split(",", 1)
            name = parts[1].strip() if len(parts) > 1 else "Toffee Channel"
            current_title = name
        elif trimmed.startswith("#EXTVLCOPT:http-user-agent="):
            current_ua = trimmed.replace("#EXTVLCOPT:http-user-agent=", "").strip()
        elif trimmed.startswith("#EXTVLCOPT:http-cookie="):
            current_cookie = trimmed.replace("#EXTVLCOPT:http-cookie=", "").strip()
        elif not trimmed.startswith("#") and trimmed.startswith("http"):
            raw_url = trimmed
            
            # যদি URL-এর ভেতরে cookie কুয়েরি প্যারাম আকারে থাকে
            if "cookie=" in trimmed:
                url_parts = trimmed.split("cookie=")
                raw_url = url_parts[0].replace(/[?&]$/, "")
                current_cookie = url_parts[1].split("&ua=")[0].split("&")[0]
            if "ua=" in trimmed:
                current_ua = trimmed.split("ua=")[1].split("&")[0]

            # URL এবং Cookie এনকোড করা
            encoded_stream_url = urllib.parse.quote(raw_url, safe="")
            
            # কুকিতে Edge-Cache-Cookie ফরম্যাট নিশ্চিত করা
            clean_cookie = current_cookie.strip()
            try:
                clean_cookie = urllib.parse.unquote(clean_cookie)
            except Exception:
                pass
            if clean_cookie and not clean_cookie.startswith("Edge-Cache-Cookie="):
                clean_cookie = f"Edge-Cache-Cookie={clean_cookie}"
                
            encoded_cookie = urllib.parse.quote(clean_cookie, safe="")

            # 🎯 আপনার কাঙ্ক্ষিত ওয়ার্কার প্রক্সি লিংক
            proxied_link = (
                f"{PROXY_BASE}?url={encoded_stream_url}"
                f"&cookie={encoded_cookie}"
                f"&secret_key={SECRET_KEY}"
            )

            channels.append({
                "title": current_title or f"Toffee Channel {len(channels) + 1}",
                "url": proxied_link
            })

            # রিসেট
            current_title = ""
            current_cookie = ""
            current_ua = "Toffee (Linux;Android 14)"

    print(f"Total processed channels: {len(channels)}")

    if not channels:
        print("No channels found!")
        return

    # নতুন M3U প্লেলিস্ট তৈরি
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for ch in channels:
            f.write(f'#EXTINF:-1 group-title="Toffee Live", {ch["title"]}\n')
            f.write(f'{ch["url"]}\n\n')

    print(f"🎉 Successfully generated {OUTPUT_FILE} with {len(channels)} active channels!")

if __name__ == "__main__":
    generate_proxy_playlist()
