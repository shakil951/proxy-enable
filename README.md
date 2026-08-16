# 📡 Toffee Proxy Playlist Auto-Updater

An automated IPTV stream generator and scraper designed for Android Media3/ExoPlayer applications. It periodically extracts active streaming sessions, binds them with a secure Cloudflare Worker proxy, and delivers a clean, tokenized M3U8 playlist.

---

### 🚀 Key Features

* **Dynamic Cookie Management:** Automatically extracts and injects active `Edge-Cache-Cookie` tokens to bypass CDN session timeouts.
* **Cloudflare Worker Routing:** Routes all streams through an authenticated reverse-proxy to manage cross-origin access and user-agent emulation.
* **Universal Media3/ExoPlayer Ready:** Formats query parameters and extensions cleanly to guarantee playback on Android OTT/IPTV players.
* **Zero-Server Maintenance:** Fully scheduled via **GitHub Actions** (Runs every 3 hours) with zero hosting costs.

---

### 📋 Direct Playlist URL

Use the following raw M3U link directly in your IPTV player or Android application:

```text
[https://raw.githubusercontent.com/shakil951/proxy-enable/main/playlist.m3u](https://raw.githubusercontent.com/shakil951/proxy-enable/main/playlist.m3u)
