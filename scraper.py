import asyncio
from playwright.async_api import async_playwright

TARGET_SITE = "https://fslivetv.vercel.app/"
OUTPUT_FILE = "playlist.m3u"

async def scrape_dynamic_streams():
    captured_streams = []

    async with async_playwright() as p:
        # ব্যাকগ্রাউন্ডে ক্রোম ব্রাউজার চালু করা
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # নেটওয়ার্ক রিকোয়েস্ট ইন্টারসেপ্ট করে জেনারেট হওয়া m3u8 লিংক ক্যাপচার
        async def handle_request(request):
            req_url = request.url
            if ".m3u8" in req_url or "workers.dev" in req_url:
                if req_url not in captured_streams and "favicon" not in req_url:
                    captured_streams.append(req_url)
                    print(f"[Captured]: {req_url[:80]}...")

        page.on("request", handle_request)

        print(f"Opening {TARGET_SITE} ...")
        await page.goto(TARGET_SITE, wait_until="networkidle", timeout=60000)

        # পেজের সব চ্যানেল বাটনে ক্লিক ট্রিগার করা যাতে লিংক জেনারেট হয়
        buttons = await page.query_selector_all("button, .channel-item, .channel-card, a")
        print(f"Found {len(buttons)} interactive elements. Triggering...")

        for i, btn in enumerate(buttons[:40]): # চ্যানেলগুলোতে ক্লিক সিমুলেট
            try:
                await btn.click(timeout=2000)
                await asyncio.sleep(1) # লিংক জেনারেট হওয়ার জন্য অপেক্ষা
            except Exception:
                pass

        await asyncio.sleep(5)
        await browser.close()

    # ইউনিক লিংক ফিল্টারিং
    unique_streams = list(dict.fromkeys(captured_streams))
    print(f"\nTotal generated streams captured: {len(unique_streams)}")

    if unique_streams:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for idx, stream_url in enumerate(unique_streams, start=1):
                f.write(f'#EXTINF:-1 group-title="Toffee Live", Channel {idx}\n')
                f.write(f"{stream_url}\n\n")
        print(f"Successfully generated {OUTPUT_FILE}")
    else:
        print("No dynamic streams could be captured.")

if __name__ == "__main__":
    asyncio.run(scrape_dynamic_streams())
