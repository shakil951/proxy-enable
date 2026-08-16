import json
import re
import requests

TARGET_SITE = "https://fslivetv.vercel.app"
OUTPUT_FILE = "playlist.m3u"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_streams():
    print(f"Fetching: {TARGET_SITE}")
    try:
        res = requests.get(TARGET_SITE, headers=headers, timeout=15)
    except Exception as e:
        print(f"Failed to fetch site: {e}")
        return

    html = res.text
    all_content = html

    # ১. সাইটের সব JS ফাইল ও Next.js / Webpack চাঙ্ক সংগ্রহ
    js_paths = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
    
    # Next.js / Vite build manifest assets
    build_manifests = re.findall(r'["\'](/_next/[^"\']+\.js)["\']', html)
    js_paths.extend(build_manifests)

    for js in set(js_paths):
        full_js_url = js if js.startswith("http") else f"{TARGET_SITE.rstrip('/')}/{js.lstrip('/')}"
        try:
            js_res = requests.get(full_js_url, headers=headers, timeout=10)
            if js_res.status_code == 200:
                all_content += "\n" + js_res.text
        except Exception:
            pass

    # ২. চ্যানেল অবজেক্ট বা সরাসরি m3u8 লিংক এক্সট্রাক্ট
    # প্যাটার্ন ১: Cloudflare Worker প্রক্সি লিংক
    worker_streams = re.findall(r'(https?://[a-zA-Z0-9_\-\.]+\.workers\.dev[^\s"\'<>`]+)', all_content)
    
    # প্যাটার্ন ২: স্ট্যান্ডার্ড HLS M3U8 লিংক
    m3u8_streams = re.findall(r'(https?://[^\s"\'<>`]+\.m3u8[^\s"\'<>`]*)', all_content)

    found_links = []
    for link in (worker_streams + m3u8_streams):
        clean_link = link.replace("\\", "").rstrip('",;\'')
        if "example.com" not in clean_link and clean_link.startswith("http"):
            found_links.append(clean_link)

    unique_streams = list(dict.fromkeys(found_links))

    print(f"Total active streams found: {len(unique_streams)}")

    if not unique_streams:
        print("Warning: No streams found. Check if site data is loaded from a separate API.")
        return

    # ৩. M3U প্লেলিস্ট জেনারেট
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for idx, stream_url in enumerate(unique_streams, start=1):
            f.write(f'#EXTINF:-1 group-title="Toffee Live", Channel {idx}\n')
            f.write(f"{stream_url}\n\n")

    print(f"Updated {OUTPUT_FILE} successfully with {len(unique_streams)} channels.")

if __name__ == "__main__":
    extract_streams()
