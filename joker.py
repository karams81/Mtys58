# -*- coding: utf-8 -*-
import re
import sys
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- AYARLAR ----------------------------------------------------------------
TARGET_URL  = "https://jokerbettvi177.com/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
CIKTI_DOSYA = "joker.m3u8"

# Cloudflare Workers proxy (VPN gerektirmez)
CF_PROXY = "https://rapid-wave-c8e3.redfor14314.workers.dev/"

URLLER = [
    CF_PROXY + "https://jokerbettvi177.com",
    CF_PROXY + "https://jokerbettvi178.com",
    CF_PROXY + "https://jokerbettvi179.com",
    CF_PROXY + "https://jokerbettvi180.com",
    "https://jokerbettvi177.com/",
    "https://jokerbettvi178.com/",
]

# --- SABIT KANALLAR ---------------------------------------------------------
SABIT_KANALLAR = [
    ("beIN SPORTS HD1",   "bein-sports-1.m3u8"),
    ("beIN SPORTS HD2",   "bein-sports-2.m3u8"),
    ("beIN SPORTS HD3",   "bein-sports-3.m3u8"),
    ("beIN SPORTS HD4",   "bein-sports-4.m3u8"),
    ("beIN SPORTS HD5",   "bein-sports-5.m3u8"),
    ("beIN SPORTS MAX 1", "bein-sports-max-1.m3u8"),
    ("beIN SPORTS MAX 2", "bein-sports-max-2.m3u8"),
    ("S SPORT",           "s-sport.m3u8"),
    ("S SPORT 2",         "s-sport-2.m3u8"),
    ("TIVIBUSPOR 1",      "tivibu-spor.m3u8"),
    ("TIVIBUSPOR 2",      "tivibu-spor-2.m3u8"),
    ("TIVIBUSPOR 3",      "tivibu-spor-3.m3u8"),
    ("TIVIBUSPOR 4",      "tivibu-spor-4.m3u8"),
    ("SPOR SMART",        "spor-smart.m3u8"),
    ("SPOR SMART 2",      "spor-smart-2.m3u8"),
    ("TRT SPOR",          "trt-spor.m3u8"),
    ("TRT SPOR 2",        "trt-spor-yildiz.m3u8"),
    ("TRT 1",             "trt-1.m3u8"),
    ("ASPOR",             "a-spor.m3u8"),
    ("TABII SPOR",        "tabii-spor.m3u8"),
    ("TABII SPOR 1",      "tabii-spor-1.m3u8"),
    ("TABII SPOR 2",      "tabii-spor-2.m3u8"),
    ("TABII SPOR 3",      "tabii-spor-3.m3u8"),
    ("TABII SPOR 4",      "tabii-spor-4.m3u8"),
    ("TABII SPOR 5",      "tabii-spor-5.m3u8"),
    ("TABII SPOR 6",      "tabii-spor-6.m3u8"),
    ("ATV",               "atv.m3u8"),
    ("TV 8.5",            "tv8.5.m3u8"),
]

# ============================================================================
def get_html():
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    for url in URLLER:
        label = "[CF-PROXY]" if CF_PROXY in url else "[DIREKT] "
        try:
            print(f"{label} {url}")
            res = requests.get(url, headers=headers, timeout=25, verify=False)
            if res.status_code == 200 and "data-stream" in res.text:
                print(f"[OK] Basarili! ({len(res.text)} byte)")
                return res.text
            print(f"[--] HTTP {res.status_code}")
        except Exception as e:
            print(f"[--] {e}")
    return None

# ============================================================================
def build_m3u8(html):
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xmlx.workers.dev/"

    # Proxy URL'si CDN olarak algilanmasin
    if "redfor14314" in base_url:
        base_url = "https://pix.xmlx.workers.dev/"

    print(f"[i]  CDN: {base_url}")

    lines = ["#EXTM3U"]

    for name, file in SABIT_KANALLAR:
        lines += [
            f'#EXTINF:-1 group-title="SABIT KANALLAR",{name}',
            f'#EXTVLCOPT:http-user-agent={UA}',
            f'#EXTVLCOPT:http-referrer={TARGET_URL}',
            f"{base_url}{file}",
        ]

    a_tags = re.findall(r'<a\s[^>]*data-stream="[^"]*"[^>]*>', html, re.DOTALL)
    seen  = set()
    count = 0
    for tag in a_tags:
        s = re.search(r'data-stream="([^"]+)"', tag)
        n = re.search(r'data-name="([^"]+)"',   tag)
        t = re.search(r'data-matchtype="([^"]+)"', tag)
        if not (s and n):
            continue
        stream_id = s.group(1)
        if stream_id in seen:
            continue
        seen.add(stream_id)

        name  = n.group(1).strip()
        sport = t.group(1) if t else "Diger"

        if stream_id.startswith("betlivematch-"):
            pure = stream_id.replace("betlivematch-", "")
            link = f"{base_url}hls/{pure}.m3u8"
        else:
            link = f"{base_url}{stream_id}.m3u8"

        lines += [
            f'#EXTINF:-1 group-title="CANLI - {sport}",{name}',
            f'#EXTVLCOPT:http-user-agent={UA}',
            f'#EXTVLCOPT:http-referrer={TARGET_URL}',
            link,
        ]
        count += 1

    print(f"[i]  {count} canli mac eklendi.")
    return "\n".join(lines)

# ============================================================================
def main():
    print("=" * 55)
    print("  Joker M3U8 Uretici")
    print("=" * 55)

    html = get_html()

    if not html:
        print("[!!] HTML alinamadi, cikiliyor.")
        sys.exit(1)  # GitHub Actions'ta hata olarak isaretle

    content = build_m3u8(html)

    with open(CIKTI_DOSYA, "w", encoding="utf-8") as f:
        f.write(content)

    total = content.count("#EXTINF")
    print(f"\n[OK] '{CIKTI_DOSYA}' olusturuldu!")
    print(f"     Sabit  : {len(SABIT_KANALLAR)}")
    print(f"     Canli  : {total - len(SABIT_KANALLAR)}")
    print(f"     Toplam : {total} kanal")
    print("=" * 55)

if __name__ == "__main__":
    main()
