import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── AYARLAR ────────────────────────────────────────────────────────────────
TARGET_URL = "https://jokerbettvi177.com/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ─── SABİT KANALLAR (listeye her zaman eklenir) ─────────────────────────────
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
    ("TABİİ SPOR",        "tabii-spor.m3u8"),
    ("TABİİ SPOR 1",      "tabii-spor-1.m3u8"),
    ("TABİİ SPOR 2",      "tabii-spor-2.m3u8"),
    ("TABİİ SPOR 3",      "tabii-spor-3.m3u8"),
    ("TABİİ SPOR 4",      "tabii-spor-4.m3u8"),
    ("TABİİ SPOR 5",      "tabii-spor-5.m3u8"),
    ("TABİİ SPOR 6",      "tabii-spor-6.m3u8"),
    ("ATV",               "atv.m3u8"),
    ("TV 8.5",            "tv8.5.m3u8"),
]

# ─── HTML ÇEKİCİ ─────────────────────────────────────────────────────────────
def get_html():
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
        "Referer": TARGET_URL,
    }

    # 1) Doğrudan bağlantı
    try:
        print(f"🔄 Doğrudan bağlanıyor: {TARGET_URL}")
        res = requests.get(TARGET_URL, headers=headers, timeout=15, verify=False)
        if res.status_code == 200 and "data-stream" in res.text:
            print("✅ Doğrudan bağlantı başarılı!")
            return res.text
        print(f"   ⚠️  HTTP {res.status_code}")
    except Exception as e:
        print(f"   ⚠️  Doğrudan bağlantı hatası: {e}")

    # 2) Proxy'ler
    proxies = [
        f"https://api.codetabs.com/v1/proxy/?quest={TARGET_URL}",
        f"https://corsproxy.io/?{TARGET_URL}",
        f"https://thingproxy.freeboard.io/fetch/{TARGET_URL}",
    ]
    for url in proxies:
        try:
            print(f"🔄 Proxy deneniyor: {url[:70]}...")
            res = requests.get(url, headers={"User-Agent": UA}, timeout=15, verify=False)
            if res.status_code == 200 and "data-stream" in res.text:
                print("✅ Proxy başarılı!")
                return res.text
            print(f"   ⚠️  HTTP {res.status_code}")
        except Exception as e:
            print(f"   ⚠️  {e}")

    return None


# ─── M3U8 OLUŞTURUCU ──────────────────────────────────────────────────────────
def build_m3u8(html: str) -> str:
    # Aktif CDN sunucusunu HTML'den bul
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xmlx.workers.dev/"
    print(f"📡 Aktif CDN Sunucu: {base_url}")

    lines = ["#EXTM3U"]

    # ── Sabit kanallar ──────────────────────────────────────────────────────
    for name, file in SABIT_KANALLAR:
        lines += [
            f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name}',
            f'#EXTVLCOPT:http-user-agent={UA}',
            f'#EXTVLCOPT:http-referrer={TARGET_URL}',
            f"{base_url}{file}",
        ]

    # ── Canlı maçlar  (<a> tag'larından data-stream + data-name) ────────────
    # Her <a ...> bloğundan attribute'ları güvenle çek
    a_tags = re.findall(r'<a\s[^>]*data-stream="[^"]*"[^>]*>', html, re.DOTALL)
    seen = set()
    count = 0

    for tag in a_tags:
        s = re.search(r'data-stream="([^"]+)"', tag)
        n = re.search(r'data-name="([^"]+)"', tag)
        t = re.search(r'data-matchtype="([^"]+)"', tag)

        if not (s and n):
            continue
        stream_id = s.group(1)
        name      = n.group(1).strip()
        sport     = t.group(1) if t else "Diğer"

        if stream_id in seen:
            continue
        seen.add(stream_id)

        # URL oluştur
        if stream_id.startswith("betlivematch-"):
            pure = stream_id.replace("betlivematch-", "")
            link = f"{base_url}hls/{pure}.m3u8"
        else:
            # Kanal kodu (s-sports-1 vb.) → doğrudan kök
            link = f"{base_url}{stream_id}.m3u8"

        group = f"⚽ CANLI - {sport}"
        lines += [
            f'#EXTINF:-1 group-title="{group}",{name}',
            f'#EXTVLCOPT:http-user-agent={UA}',
            f'#EXTVLCOPT:http-referrer={TARGET_URL}',
            link,
        ]
        count += 1

    print(f"⚽ {count} canlı maç eklendi.")
    return "\n".join(lines)


# ─── ANA FONKSİYON ───────────────────────────────────────────────────────────
def main():
    html = get_html()

    if not html:
        print("\n❌ Siteye ulaşılamadı!")
        print("💡 İpucu:")
        print("   • VPN açıp tekrar deneyin")
        print("   • TARGET_URL'yi güncel adresle değiştirin (jokerbet899.com vb.)")
        return

    content = build_m3u8(html)

    out_file = "joker.m3u8"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    total = content.count("#EXTINF")
    print(f"\n🚀 Tamamlandı! → {out_file}")
    print(f"   📺 Sabit kanallar : {len(SABIT_KANALLAR)}")
    print(f"   ⚽ Canlı maçlar   : {total - len(SABIT_KANALLAR)}")
    print(f"   📋 Toplam         : {total} kanal")


if __name__ == "__main__":
    main()
