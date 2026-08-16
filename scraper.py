import asyncio
import re
from playwright.async_api import async_playwright

TARGET_SITE = "https://fslivetv.vercel.app/"
OUTPUT_FILE = "playlist.m3u"

async def scrape_toffee_streams():
    captured_channels = []  # List of tuples: (channel_title, stream_url)
    seen_urls = set()
    current_title = "Toffee Live Channel"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # নেটওয়ার্ক ইন্টারসেপ্টর: শুধুমাত্র নির্দিষ্ট তোফি প্রক্সি লিঙ্ক ক্যাপচার করবে
        async def handle_request(request):
            req_url = request.url
            
            # শুধুমাত্র তোফি প্রক্সি লিঙ্ক ফিল্টার
            is_valid_toffee = (
                "toffee-proxy.usergamil15.workers.dev" in req_url and
                "url=" in req_url and
                ("toffee" in req_url.lower() or "bldcmprod" in req_url.lower())
            )

            # সাব-সেগমেন্ট / চাঙ্ক বাদ দিয়ে মূল প্লেলিস্ট লিঙ্ক রাখা
            if is_valid_toffee and not req_url.endswith(".ts") and not req_url.endswith(".m4s"):
                if req_url not in seen_urls:
                    seen_urls.add(req_url)
                    captured_channels.append({
                        "name": current_title,
                        "url": req_url
                    })
                    print(f"✅ [Captured]: {current_title} -> {req_url[:80]}...")

        page.on("request", handle_request)

        print(f"Loading {TARGET_SITE} ...")
        try:
            await page.goto(TARGET_SITE, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print(f"Navigation note: {e}")

        await asyncio.sleep(4)

        # চ্যানেল কন্টেইনার এবং বাটনের তালিকা খোঁজা
        selectors = [
            "button",
            ".channel-item",
            ".channel-card",
            ".channel-btn",
            "[role='button']",
            "li[onclick]",
            "div[onclick]"
        ]
        
        all_elements = []
        for selector in selectors:
            elems = await page.query_selector_all(selector)
            if elems:
                all_elements.extend(elems)

        print(f"Found {len(all_elements)} clickable targets. Starting full scan...")

        # পেজ বা চ্যানেল কন্টেইনার স্ক্রোল করা যাতে সব চ্যানেল লোড হয়
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(0.5)

        # প্রতিটি চ্যানেল এলিমেন্টে ক্লিক ট্রিগার করা
        for index, elem in enumerate(all_elements):
            try:
                # চ্যানেল নাম বের করা
                text = (await elem.inner_text()).strip().replace("\n", " ")
                if text and len(text) < 40 and not any(skip in text.lower() for skip in ["play", "pause", "mute", "fullscreen", "settings"]):
                    current_title = text
                else:
                    current_title = f"Toffee Channel {len(captured_channels) + 1}"

                # স্ক্রোলে এনে ক্লিক
                await elem.scroll_into_view_if_needed()
                await elem.click(timeout=1200)
                await asyncio.sleep(1) # রিকোয়েস্ট তৈরি হওয়ার জন্য ১ সেকেন্ড বিরতি
            except Exception:
                continue

        # শেষ মুহূর্তের রিকোয়েস্টের জন্য অতিরিক্ত সময়
        await asyncio.sleep(4)
        await browser.close()

    print(f"\n🎯 Total unique Toffee streams collected: {len(captured_channels)}")

    # M3U ফাইল তৈরি
    if captured_channels:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for idx, item in enumerate(captured_channels, start=1):
                f.write(f'#EXTINF:-1 group-title="Toffee Live", {item["name"]}\n')
                f.write(f'{item["url"]}\n\n')
        print(f"🎉 Successfully written to {OUTPUT_FILE}")
    else:
        print("⚠️ No matching Toffee proxy streams found.")

if __name__ == "__main__":
    asyncio.run(scrape_toffee_streams())
