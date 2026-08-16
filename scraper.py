import asyncio
import urllib.parse
from playwright.async_api import async_playwright

TARGET_SITE = "https://fslivetv.vercel.app/"
OUTPUT_FILE = "playlist.m3u"

async def scrape_all_toffee_channels():
    final_playlist = []
    seen_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        active_channel_name = ""
        
        # নেটওয়ার্ক ইন্টারসেপ্টর: শুধুমাত্র ভ্যালিড কুকি সহ তোফি লিঙ্ক ধরবে
        async def on_request(request):
            nonlocal active_channel_name
            req_url = request.url

            # শুধুমাত্র বৈধ কুকি থাকা তোফি প্রক্সি লিংক ফিল্টার
            is_toffee_proxy = "toffee-proxy.usergamil15.workers.dev" in req_url
            has_valid_cookie = "Edge-Cache-Cookie" in req_url
            is_valid_manifest = ("playlist.m3u8" in req_url or "mono.m3u8" in req_url or ".m3u8" in req_url)
            is_not_chunk = not req_url.endswith(".ts") and not req_url.endswith(".m4s")

            if is_toffee_proxy and has_valid_cookie and is_valid_manifest and is_not_chunk:
                if req_url not in seen_urls:
                    seen_urls.add(req_url)
                    name = active_channel_name if active_channel_name else f"Toffee Channel {len(final_playlist) + 1}"
                    final_playlist.append({
                        "title": name,
                        "url": req_url
                    })
                    print(f"✅ Captured: [{name}] -> {req_url[:85]}...")

        page.on("request", on_request)

        print(f"Opening {TARGET_SITE} ...")
        await page.goto(TARGET_SITE, wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(5)

        # যদি পেজে 'Toffee' বা লাইভ টিভি ক্যাটাগরি ট্যাব থাকে, সেটাতে ক্লিক
        try:
            tabs = await page.query_selector_all("button, div[role='tab'], a, span")
            for tab in tabs:
                txt = (await tab.inner_text()).strip().lower()
                if "toffee" in txt or "live tv" in txt or "bangla" in txt:
                    await tab.click()
                    await asyncio.sleep(2)
                    break
        except Exception:
            pass

        # সব চ্যানেল কার্ড বা বাটন খুঁজে বের করা
        channel_elements = await page.query_selector_all(
            ".channel-card, .channel-item, .card, button, div[onclick], [role='button']"
        )
        print(f"Total channel targets found: {len(channel_elements)}")

        for index, elem in enumerate(channel_elements):
            try:
                # চ্যানেলের নাম রিড করা
                raw_text = (await elem.inner_text()).strip()
                lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                clean_name = lines[0] if lines else f"Channel {index + 1}"

                # অপ্রয়োজনীয় প্লেয়ার কন্ট্রোল বাটন ফিল্টার
                skip_keywords = ["play", "pause", "mute", "live", "hd", "settings", "fullscreen", "00:", "volume", "home"]
                if clean_name.lower() in skip_keywords or len(clean_name) > 30:
                    continue

                active_channel_name = clean_name

                # কার্ডে স্ক্রোল করে ক্লিক দেওয়া
                await elem.scroll_into_view_if_needed()
                await elem.click(force=True, timeout=2000)
                
                # রিকোয়েস্ট তৈরি হতে পর্যাপ্ত সময় দেওয়া
                await asyncio.sleep(1.8)

            except Exception:
                continue

        # ব্যাকগ্রাউন্ড রিকোয়েস্ট শেষ করার সময়
        await asyncio.sleep(3)
        await browser.close()

    print(f"\n🎯 Total Valid Working Toffee Streams: {len(final_playlist)}")

    # M3U ফাইল লেখা
    if final_playlist:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for item in final_playlist:
                f.write(f'#EXTINF:-1 group-title="Toffee Live", {item["title"]}\n')
                f.write(f'{item["url"]}\n\n')
        print(f"🎉 Successfully written working playlist to {OUTPUT_FILE}")
    else:
        print("⚠️ No valid Toffee streams found.")

if __name__ == "__main__":
    asyncio.run(scrape_all_toffee_channels())
