import asyncio
from playwright.async_api import async_playwright

TARGET_SITE = "https://fslivetv.vercel.app/"
OUTPUT_FILE = "playlist.m3u"

async def scrape_dynamic_streams():
    captured_streams = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # নেটওয়ার্ক ইন্টারসেপ্টর
        async def handle_request(request):
            req_url = request.url
            if (".m3u8" in req_url or "workers.dev" in req_url) and "favicon" not in req_url:
                if req_url not in captured_streams:
                    captured_streams.append(req_url)
                    print(f"[Captured]: {req_url}")

        page.on("request", handle_request)

        print(f"Opening {TARGET_SITE} ...")
        try:
            # domcontentloaded ব্যবহার করায় পেজ লোড হওয়া মাত্রই কাজ শুরু করবে
            await page.goto(TARGET_SITE, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation warning (proceeding anyway): {e}")

        # প্রাথমিক স্ক্রিপ্ট এক্সিকিউট হওয়ার জন্য ৩ সেকেন্ড অপেক্ষা
        await asyncio.sleep(3)

        # পেজের সব বাটন ও চ্যানেল এলিমেন্ট খোঁজা
        buttons = await page.query_selector_all("button, .channel-item, .channel-card, div[role='button'], a")
        print(f"Found {len(buttons)} clickable elements. Triggering streams...")

        # চ্যানেলগুলোতে ক্লিক করে লাইভ লিঙ্কগুলো অ্যাক্টিভেট করা
        for i, btn in enumerate(buttons):
            try:
                await btn.click(timeout=1500)
                await asyncio.sleep(1.2)
            except Exception:
                pass

        # ব্যাকগ্রাউন্ড রিকোয়েস্ট শেষ হতে অতিরিক্ত সময়
        await asyncio.sleep(4)
        await browser.close()

    # মাস্টার ও চ্যাঙ্ক ফিল্টারিং (শুধুমাত্র মূল প্লেলিস্ট ও প্রক্সি লিংক রাখা)
    valid_streams = []
    for link in captured_streams:
        # সেগমেন্ট বা চ্যাঙ্ক (.ts / .m4s) বাদ দিয়ে মূল .m3u8 / প্রক্সি লিংক রাখা
        if not link.endswith(".ts") and not link.endswith(".m4s"):
            valid_streams.append(link)

    unique_streams = list(dict.fromkeys(valid_streams))
    print(f"\n✅ Total valid streams captured: {len(unique_streams)}")

    if unique_streams:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for idx, stream_url in enumerate(unique_streams, start=1):
                f.write(f'#EXTINF:-1 group-title="Live TV", Channel {idx}\n')
                f.write(f"{stream_url}\n\n")
        print(f"Successfully generated {OUTPUT_FILE}")
    else:
        print("No dynamic streams captured.")

if __name__ == "__main__":
    asyncio.run(scrape_dynamic_streams())
