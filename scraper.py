import re
import urllib.parse
import requests

GITHUB_SOURCE_M3U = "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/refs/heads/main/toffee_playlist.m3u"
PROXY_BASE = "https://toffee-proxy.usergamil15.workers.dev/"
SECRET_KEY = "FS_LIVE_TV_SECRET_2026"
OUTPUT_FILE = "playlist.m3u"

def clean_cookie_format(raw_cookie_str):
    if not raw_cookie_str:
        return ""
    
    # প্রথমে কোনো আগের এনকোডিং থাকলে ডিকোড করে প্লেইন টেক্সট করা
    cookie_text = raw_cookie_str.strip()
    while "%" in cookie_text:
        try:
            decoded = urllib.parse.unquote(cookie_text)
            if decoded == cookie_text:
                break
            cookie_text = decoded
        except Exception:
            break

    # Edge-Cache-Cookie প্রিফিক্স বাদ দিয়ে শুধু ভ্যালু বের করা
    if "Edge-Cache-Cookie=" in cookie_text:
        cookie_text = cookie_text.split("Edge-Cache-Cookie=")[-1]
    
    cookie_text = cookie_text.strip("; ")
    
    # টুফির সঠিক স্ট্রাকচার নিশ্চিত করা
    full_cookie_plain = f"Edge-Cache-Cookie={cookie_text}"
    
    # ফাইনাল সিঙ্গেল URL Encode (যেমন: = হবে %3D, : হবে %3A)
    return urllib.parse.quote(full_cookie_plain, safe="")

def generate_proxy_playlist():
    print(f"Fetching source playlist from: {GITHUB_SOURCE_M3U}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        res = requests.get(GITHUB_SOURCE_M3U, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch source. Status code: {res.status_code}")
            return
    except Exception as e:
        print(f"Network error: {e}")
        return

    lines = res.text.replace("\r", "").split("\n")
    
    parsed_items = []
    current_title = ""
    current_cookie = ""
    master_cookie = ""

    # ১ম পাস: ডেটা এক্সট্রাক্ট করা ও গ্লোবাল লাইভ কুকি সংরক্ষণ
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue

        if trimmed.startswith("#EXTINF:"):
            parts = trimmed.split(",", 1)
            current_title = parts[1].strip() if len(parts) > 1 else "Toffee Channel"
        elif trimmed.startswith("#EXTVLCOPT:http-cookie="):
            current_cookie = trimmed.replace("#EXTVLCOPT:http-cookie=", "").strip()
            if "URLPrefix" in current_cookie:
                master_cookie = current_cookie
        elif not trimmed.startswith("#") and trimmed.startswith("http"):
            raw_url = trimmed
            
            if "cookie=" in trimmed:
                parts = trimmed.split("cookie=")
                raw_url = re.sub(r'[?&]$', '', parts[0])
                cookie_val = parts[1].split("&ua=")[0].split("&")[0]
                if "URLPrefix" in cookie_val:
                    master_cookie = cookie_val
                    current_cookie = cookie_val

            parsed_items.append({
                "title": current_title or "Toffee Live Channel",
                "raw_url": raw_url,
                "cookie": current_cookie
            })

            current_title = ""
            current_cookie = ""

    # যদি কোনো চ্যানেলের আলাদা কুকি মিস থাকে, গ্লোবাল master_cookie ব্যবহার হবে
    final_encoded_cookie = clean_cookie_format(master_cookie)

    if not final_encoded_cookie:
        print("❌ Error: No valid Edge-Cache-Cookie found in source playlist!")
        return

    print(f"✅ Extracted Active Master Cookie successfully.")

    # ২য় পাস: আপনার এক্স্যাক্ট ওয়ার্কিং প্রক্সি লিঙ্কে রূপান্তর
    final_channels = []
    for item in parsed_items:
        raw_url = item["raw_url"]
        
        # নিশ্চিত করা যে URL-এ ডাবল প্যারাম বা অপ্রয়োজনীয় স্ল্যাশ নেই
        encoded_url = urllib.parse.quote(raw_url, safe="")

        # হুবহু আপনার চাহিদামতো লিংক ফরম্যাট
        proxied_link = (
            f"{PROXY_BASE}?url={encoded_url}"
            f"&cookie={final_encoded_cookie}"
            f"&secret_key={SECRET_KEY}"
        )

        final_channels.append({
            "title": item["title"],
            "url": proxied_link
        })

    # M3U প্লেলিস্ট তৈরি
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for ch in final_channels:
            f.write(f'#EXTINF:-1 group-title="Toffee Live", {ch["title"]}\n')
            f.write(f'{ch["url"]}\n\n')

    print(f"🎉 Generated {OUTPUT_FILE} with {len(final_channels)} perfectly formatted channels!")

if __name__ == "__main__":
    generate_proxy_playlist()
