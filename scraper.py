import re
import requests

TARGET_SITE = "https://fslivetv.vercel.app/"
OUTPUT_FILE = "playlist.m3u"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def extract_streams():
    print(f"Fetching source from: {TARGET_SITE}")
    res = requests.get(TARGET_SITE, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch site: {res.status_code}")
        return

    html = res.text

    # সাইট থেকে জাভাস্ক্রিপ্ট / সোর্স ফাইল খুঁজে বের করা
    js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
    all_content = html

    for js_url in js_files:
        if not js_url.startswith("http"):
            js_url = TARGET_SITE.rstrip("/") + "/" + js_url.lstrip("/")
        try:
            js_res = requests.get(js_url, headers=headers)
            if js_res.status_code == 200:
                all_content += "\n" + js_res.text
        except Exception:
            pass

    # প্রক্সি / m3u8 স্ট্রিম লিংক বের করার রেগুলার এক্সপ্রেশন
    # উদাহরণ: https://...workers.dev/...m3u8 বা ?url=...
    stream_pattern = r'(https?://[^\s"\'<>]+\.workers\.dev[^\s"\'<>]*\.m3u8[^\s"\'<>]*)'
    streams = re.findall(stream_pattern, all_content)
    unique_streams = list(dict.fromkeys(streams))

    if not unique_streams:
        # বিকল্প সাধারণ m3u8 লিংক প্যাটার্ন
        unique_streams = list(dict.fromkeys(re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', all_content)))

    print(f"Found {len(unique_streams)} active streams.")

    # M3U ফাইল তৈরি
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for idx, url in enumerate(unique_streams, start=1):
            f.write(f'#EXTINF:-1 group-title="Toffee Live", Toffee Channel {idx}\n')
            f.write(f"{url}\n\n")

    print(f"Successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_streams()
