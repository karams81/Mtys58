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

# ─── SABİT KANALLAR ─────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────────────────────
# SEÇENEK A — Tarayıcıdan kaydettiğin HTML dosyası
# Siteyi aç (VPN ile) → Ctrl+U (Kaynak) → Ctrl+A, Ctrl+C → txt/html olarak kaydet
# Bu scriptle aynı klasöre "html_source.html" adıyla koy.
HTML_DOSYA = "html_source.html"

# SEÇENEK B — Deneyecek URL listesi (güncel mirror adresleri ekle)
ALTERNATIF_URLLER = [
    "https://jokerbettvi177.com/",
    "https://jokerbettvi178.com/",
    "https://jokerbettvi179.com/",
    "https://jokerbettvi180.com/",
    # Yeni adresi buraya ekle:
    # "https://jokerbettvi181.com/",
]
# ────────────────────────────────────────────────────────────────────────────


def get_html_from_file():
    try:
        with open(HTML_DOSYA, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "data-stream" in content:
            print(f"✅ '{HTML_DOSYA}' dosyasından okundu.")
            return content
        print(f"⚠️  '{HTML_DOSYA}' var ama içinde maç verisi yok.")
    except FileNotFoundError:
        pass
    return None


def get_html_from_web():
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
    }
    # Direkt URL'ler
    for url in ALTERNATIF_URLLER:
        try:
            print(f"🔄 Bağlanıyor: {url}")
            res = requests.get(url, headers=headers, timeout=15, verify=False)
            if res.status_code == 200 and "data-stream" in res.text:
                print(f"✅ Başarılı!")
                return res.text
            print(f"   ⚠️  HTTP {res.status_code}")
        except Exception as e:
            print(f"   ⚠️  {e}")

    # Proxy servisleri
    base = ALTERNATIF_URLLER[0]
    proxies = [
        f"https://api.allorigins.win/raw?url={base}",
        f"https://api.codetabs.com/v1/proxy/?quest={base}",
        f"https://corsproxy.io/?{base}",
    ]
    for url in proxies:
        try:
            print(f"🔄 Proxy: {url[:70]}...")
            res = requests.get(url, headers={"User-Agent": UA}, timeout=20, verify=False)
            if res.status_code == 200 and "data-stream" in res.text:
                print("✅ Proxy başarılı!")
                return res.text
            print(f"   ⚠️  HTTP {res.status_code}")
        except Exception as e:
            print(f"   ⚠️  {e}")

    return None


def build_m3u8(html):
    # CDN sunucusunu bul
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xmlx.workers.dev/"
    print(f"📡 CDN Sunucu: {base_url}")

    lines = ["#EXTM3U"]

    # Sabit kanallar
    for name, file in SABIT_KANALLAR:
        lines += [
            f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name}',
            f'#EXTVLCOPT:http-user-agent={UA}',
            f'#EXTVLCOPT:http-referrer={TARGET_URL}',
            f"{base_url}{file}",
        ]

    # Canlı maçlar — <a> taglarından çek
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
        if stream_id in seen:
            continue
        seen.add(stream_id)

        name  = n.group(1).strip()
        sport = t.group(1) if t else "Diğer"

        if stream_id.startswith("betlivematch-"):
            pure = stream_id.replace("betlivematch-", "")
            link = f"{base_url}hls/{pure}.m3u8"
        else:
            link = f"{base_url}{stream_id}.m3u8"

        lines += [
            f'#EXTINF:-1 group-title="⚽ CANLI - {sport}",{name}',
            f'#EXTVLCOPT:http-user-agent={UA}',
            f'#EXTVLCOPT:http-referrer={TARGET_URL}',
            link,
        ]
        count += 1

    print(f"⚽ {count} canlı maç eklendi.")
    return "\n".join(lines)


def main():
    # 1) HTML dosyası varsa kullan
    html = get_html_from_file()

    # 2) Yoksa web'den çek
    if not html:
        print(f"\n📁 '{HTML_DOSYA}' bulunamadı, web'den çekmeye çalışıyor...\n")
        html = get_html_from_web()

    # 3) Yine de yoksa kullanıcıya talimat ver
    if not html:
        print("\n❌ HTML alınamadı!\n")
        print("=" * 60)
        print("ÇÖZÜM — Manuel HTML Kaydetme:")
        print("=" * 60)
        print(f"1. VPN aç")
        print(f"2. Tarayıcında aç: {TARGET_URL}")
        print(f"3. Ctrl+U → Sayfa kaynağı açılır")
        print(f"4. Ctrl+A, Ctrl+C ile tümünü kopyala")
        print(f"5. Notepad/VSCode'da yeni dosya oluştur")
        print(f"6. '{HTML_DOSYA}' adıyla bu scriptyle aynı")
        print(f"   klasöre kaydet")
        print(f"7. python joker_gen.py  →  tekrar çalıştır")
        print("=" * 60)
        return

    content = build_m3u8(html)

    with open("joker.m3u8", "w", encoding="utf-8") as f:
        f.write(content)

    total = content.count("#EXTINF")
    print(f"\n🚀 Tamamlandı! → joker.m3u8")
    print(f"   📺 Sabit kanallar : {len(SABIT_KANALLAR)}")
    print(f"   ⚽ Canlı maçlar   : {total - len(SABIT_KANALLAR)}")
    print(f"   📋 Toplam         : {total} kanal")


if __name__ == "__main__":
    main()
