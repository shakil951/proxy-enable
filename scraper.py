import re
import requests

# নতুন সোর্স লিংক আপডেট করা হলো
SOURCE_URLS = [
    "https://raw.githubusercontent.com/srhady/toffee-bd/refs/heads/main/toffee_playlist.m3u"
]

PROXY_BASE = "https://toffee-proxy.usergamil15.workers.dev/"
OUTPUT_FILE = "playlist.m3u"

def get_source():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for url in SOURCE_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200 and len(r.text) > 100:
                return r.text
        except Exception:
            pass
    return None

def build_playlist():
    content = get_source()
    if not content:
        print("Source fetch failed")
        return

    lines = content.replace("\r", "").split("\n")
    out_lines = ["#EXTM3U\n"]
    current_logo = ""
    current_name = ""
    current_group = "Toffee Live"

    for line in lines:
        l = line.strip()
        if not l: continue

        if l.startswith("#EXTINF:"):
            logo_m = re.search(r'tvg-logo="([^"]+)"', l)
            current_logo = logo_m.group(1) if logo_m else ""

            group_m = re.search(r'group-title="([^"]+)"', l)
            current_group = group_m.group(1) if group_m else "Toffee Live"

            if "," in l:
                current_name = l.split(",")[-1].strip()
            else:
                current_name = "Toffee Channel"

        elif not l.startswith("#") and ("http://" in l or "https://" in l):
            channel_id = "unknown_channel"
            match = re.search(r'/([^/]+)/(?:playlist|index)\.m3u8', l)
            if match:
                channel_id = match.group(1)

            final_proxy_url = f"{PROXY_BASE}{channel_id}/index.m3u8"

            ch_name = current_name if current_name else "Toffee Channel"
            tag_line = f'#EXTINF:-1 tvg-id="{ch_name}" tvg-name="{ch_name}" tvg-logo="{current_logo}" group-title="{current_group}",{ch_name}'
            
            out_lines.append(f"{tag_line}\n{final_proxy_url}\n")
            
            current_logo = ""
            current_name = ""
            current_group = "Toffee Live"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"Generated CLEAN playlist with {len(out_lines)-1} entries.")

if __name__ == "__main__":
    build_playlist()
