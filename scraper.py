import re
import urllib.parse
import requests

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
                print("✅ Successfully loaded source file.")
                return res.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
    return None

def extract_master_cookie(content):
    cookie_match = re.search(r'(URLPrefix%3D[^\s"\'\n\r&]+|URLPrefix=[^\s"\'\n\r&]+)', content)
    if cookie_match:
        raw_cookie = cookie_match.group(1)
        clean_cookie = urllib.parse.unquote(raw_cookie)
        if not clean_cookie.startswith("Edge-Cache-Cookie="):
            clean_cookie = f"Edge-Cache-Cookie={clean_cookie}"
        return urllib.parse.quote(clean_cookie, safe="")
    return ""

def generate_proxy_playlist():
    content = fetch_source_text()
    if not content:
        print("❌ Error: Could not fetch source playlist from any URL.")
        return

    encoded_cookie = extract_master_cookie(content)
    print(f"Extracted Cookie Status: {'FOUND' if encoded_cookie else 'NOT FOUND'}")

    lines = content.replace("\r", "").split("\n")
    channels = []
    current_extinf = ""

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue

        # সম্পূর্ণ EXTINF লাইন (tvg-logo, tvg-id, group-title) অক্ষত রাখা
        if trimmed.startswith("#EXTINF:"):
            current_extinf = trimmed
        elif not trimmed.startswith("#") and ("http://" in trimmed or "https://" in trimmed):
            raw_url = trimmed
            
            # অতিরিক্ত প্যারামিটার ক্লিন করা
            if "cookie=" in raw_url:
                raw_url = raw_url.split("cookie=")[0]
            if "url=" in raw_url and "workers.dev" in raw_url:
                extracted = re.search(r'url=([^&]+)', raw_url)
                if extracted:
                    raw_url = urllib.parse.unquote(extracted.group(1))

            raw_url = re.sub(r'[?&]$', '', raw_url)
            
            if "bldcmprod-cdn" in raw_url or "toffeelive" in raw_url or ".m3u8" in raw_url:
                encoded_stream_url = urllib.parse.quote(raw_url, safe="")

                # ওয়ার্কার প্রক্সি লিঙ্ক
                proxied_url = (
                    f"{PROXY_BASE}?url={encoded_stream_url}"
                    f"&cookie={encoded_cookie}"
                    f"&secret_key={SECRET_KEY}"
                )

                # যদি সোর্সে কোনো কারণে EXTINF মিস থাকে
                final_extinf = current_extinf if current_extinf else f'#EXTINF:-1 group-title="Toffee Live", Toffee Channel {len(channels) + 1}'

                channels.append({
                    "extinf": final_extinf,
                    "url": proxied_url
                })

            current_extinf = ""

    print(f"Total valid channels found: {len(channels)}")

    if not channels:
        print("❌ No channels parsed.")
        return

    # M3U ফাইলে সংরক্ষণ
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for ch in channels:
            f.write(f'{ch["extinf"]}\n')
            f.write(f'{ch["url"]}\n\n')

    print(f"🎉 Successfully generated {OUTPUT_FILE} with full Logos and Metadata!")

if __name__ == "__main__":
    generate_proxy_playlist()
