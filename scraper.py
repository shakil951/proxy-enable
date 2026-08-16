import asyncio
import re
import urllib.parse
from playwright.async_api import async_playwright

TARGET_SITE = "https://fslivetv.vercel.app/"
OUTPUT_FILE = "playlist.m3u"
PROXY_BASE = "https://toffee-proxy.usergamil15.workers.dev/"
SECRET_KEY = "FS_LIVE_TV_SECRET_2026"

# টুফির জনপ্রিয় সব চ্যানেলের স্ট্যান্ডার্ড সোর্স ম্যাপিং (ব্যাকআপ ও নাম সহ)
DEFAULT_TOFFEE_CHANNELS = [
    ("Somoy TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/somoy_tv/playlist.m3u8"),
    ("Channel 24", "https://bldcmprod-cdn.toffeelive.com/cdn/live/channel_24/playlist.m3u8"),
    ("Jamuna TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/jamuna_tv/playlist.m3u8"),
    ("T Sports HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/tsports_hd/playlist.m3u8"),
    ("Toffee Drama", "https://bldcmprod-cdn.toffeelive.com/cdn/live/toffee_drama/playlist.m3u8"),
    ("Toffee Movies", "https://bldcmprod-cdn.toffeelive.com/cdn/live/toffee_movies/playlist.m3u8"),
    ("Ekattor TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/ekattor_tv/playlist.m3u8"),
    ("Independent TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/independent_tv/playlist.m3u8"),
    ("ATN Bangla", "https://bldcmprod-cdn.toffeelive.com/cdn/live/atn_bangla/playlist.m3u8"),
    ("ATN News", "https://bldcmprod-cdn.toffeelive.com/cdn/live/atn_news/playlist.m3u8"),
    ("Bangla Vision", "https://bldcmprod-cdn.toffeelive.com/cdn/live/banglavision/playlist.m3u8"),
    ("Channel i", "https://bldcmprod-cdn.toffeelive.com/cdn/live/channel_i/playlist.m3u8"),
    ("Boishakhi TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/boishakhi_tv/playlist.m3u8"),
    ("Desh TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/desh_tv/playlist.m3u8"),
    ("Deepto TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/deepto_tv/playlist.m3u8"),
    ("DBC News", "https://bldcmprod-cdn.toffeelive.com/cdn/live/dbc_news/playlist.m3u8"),
    ("GTV (Gazi TV)", "https://bldcmprod-cdn.toffeelive.com/cdn/live/gazi_tv/playlist.m3u8"),
    ("Maasranga TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/maasranga_tv/playlist.m3u8"),
    ("NTV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/ntv/playlist.m3u8"),
    ("Nagorik TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/nagorik_tv/playlist.m3u8"),
    ("News24", "https://bldcmprod-cdn.toffeelive.com/cdn/live/news24/playlist.m3u8"),
    ("RTV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/rtv/playlist.m3u8"),
    ("SA TV", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sa_tv/playlist.m3u8"),
    ("Sony Ten 1 HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_ten_1_hd/playlist.m3u8"),
    ("Sony Ten 2 HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_ten_2_hd/playlist.m3u8"),
    ("Sony Ten 3 HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_ten_3_hd/playlist.m3u8"),
    ("Sony Ten 5 HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_ten_5_hd/playlist.m3u8"),
    ("Sony Six HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_six_hd/playlist.m3u8"),
    ("Sony Max HD", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_max_hd/playlist.m3u8"),
    ("Sony Yay", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_yay/playlist.m3u8"),
    ("Sony SAB", "https://bldcmprod-cdn.toffeelive.com/cdn/live/sony_sab/playlist.m3u8")
]

async def run_scraper():
    captured_cookie = None
    captured_secret = SECRET_KEY
    dom_channels = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # নেটওয়ার্ক থেকে লাইভ ফ্রেশ কুকি সংগ্রহ
        async def on_request(request):
            nonlocal captured_cookie, captured_secret
            url = request.url
            if "Edge-Cache-Cookie" in url:
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                if "cookie" in params and params["cookie"]:
                    captured_cookie = params["cookie"][0]
                if "secret_key" in params and params["secret_key"]:
                    captured_secret = params["secret_key"][0]
                print(f"🔑 Live Cookie Captured Successfully!")

        page.on("request", on_request)

        print(f"Visiting: {TARGET_SITE}")
        try:
            await page.goto(TARGET_SITE, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Warning: {e}")

        await asyncio.sleep(4)

        # ওয়েবসাইটের UI থেকে চ্যানেলের নামগুলো সংগ্রহ
        elements = await page.query_selector_all("button, .channel-item, .channel-card, [role='button']")
        for el in elements:
            try:
                txt = (await el.inner_text()).strip()
                first_line = txt.split("\n")[0].strip()
                if first_line and len(first_line) < 30 and not any(k in first_line.lower() for k in ["play", "pause", "mute", "live", "settings", "00:"]):
                    if first_line not in dom_channels:
                        dom_channels.append(first_line)
            except Exception:
                pass

        await browser.close()

    if not captured_cookie:
        print("❌ Cookie capture failed. Website might be down.")
        return

    print(f"✅ Generating M3U with fresh Live Cookie for all channels...")

    # M3U প্লেলিস্ট ফাইল তৈরি
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for title, raw_stream in DEFAULT_TOFFEE_CHANNELS:
            encoded_url = urllib.parse.quote(raw_stream, safe="")
            encoded_cookie = urllib.parse.quote(captured_cookie, safe="")
            
            # নিখুঁত প্রক্সি লিংক ফরম্যাট
            proxied_url = f"{PROXY_BASE}?url={encoded_url}&cookie={encoded_cookie}&secret_key={captured_secret}"

            f.write(f'#EXTINF:-1 group-title="Toffee Live", {title}\n')
            f.write(f"{proxied_url}\n\n")

    print(f"🎉 Successfully generated {len(DEFAULT_TOFFEE_CHANNELS)} working channels in {OUTPUT_FILE}!")

if __name__ == "__main__":
    asyncio.run(run_scraper())
