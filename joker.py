import re
import cloudscraper # requests yerine cloudflare aşan scraper kullanıyoruz
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
TARGET_URL = "https://jokerbettv177.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# SABİT KANALLAR LİSTESİ
SABIT_KANALLAR = [
    ("beIN SPORTS HD1", "bein-sports-1.m3u8"),
    ("beIN SPORTS HD2", "bein-sports-2.m3u8"),
    ("beIN SPORTS HD3", "bein-sports-3.m3u8"),
    ("beIN SPORTS HD4", "bein-sports-4.m3u8"),
    ("beIN SPORTS HD5", "bein-sports-5.m3u8"),
    ("beIN SPORTS MAX 1", "bein-sports-max-1.m3u8"),
    ("beIN SPORTS MAX 2", "bein-sports-max-2.m3u8"),
    ("S SPORT", "s-sport.m3u8"),
    ("S SPORT 2", "s-sport-2.m3u8"),
    ("TIVIBUSPOR 1", "tivibu-spor.m3u8"),
    ("TIVIBUSPOR 2", "tivibu-spor-2.m3u8"),
    ("TIVIBUSPOR 3", "tivibu-spor-3.m3u8"),
    ("TIVIBUSPOR 4", "tivibu-spor-4.m3u8"),
    ("spor SMART", "spor-smart.m3u8"),
    ("spor SMART 2", "spor-smart-2.m3u8"),
    ("TRT SPOR", "trt-spor.m3u8"),
    ("TRT SPOR 2", "trt-spor-yildiz.m3u8"),
    ("TRT 1", "trt-1.m3u8"),
    ("ASPOR", "a-spor.m3u8"),
    ("TABİİ SPOR", "tabii-spor.m3u8"),
    ("TABİİ SPOR 1", "tabii-spor-1.m3u8"),
    ("TABİİ SPOR 2", "tabii-spor-2.m3u8"),
    ("TABİİ SPOR 3", "tabii-spor-3.m3u8"),
    ("TABİİ SPOR 4", "tabii-spor-4.m3u8"),
    ("TABİİ SPOR 5", "tabii-spor-5.m3u8"),
    ("TABİİ SPOR 6", "tabii-spor-6.m3u8"),
    ("ATV", "atv.m3u8"),
    ("TV 8.5", "tv8.5.m3u8")
]

def get_html():
    # Cloudflare korumasını aşmak için scraper oluşturuyoruz
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        print(f"🔄 Güvenlik duvarı aşılıyor: {TARGET_URL}")
        # Doğrudan siteye istek atıyoruz, scraper engelleri temizleyecektir
        res = scraper.get(TARGET_URL, timeout=20)
        
        if res.status_code == 200:
            print("✅ Site içeriği başarıyla alındı.")
            return res.text
        else:
            print(f"⚠️ Hata Kodu: {res.status_code}")
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
    
    return None

def main():
    html = get_html()
    if not html:
        print("❌ Siteye ulaşılamadı. VPN açık olduğundan emin olun veya DNS değiştirin.")
        return

    # 1. GÜNCEL SUNUCUYU BUL (Workers.dev linkini yakalar)
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xsiic.workers.dev/"
    print(f"📡 Aktif Sunucu: {base_url}")

    m3u = ["#EXTM3U"]

    # 2. SABİT KANALLARI EKLE
    for name, file in SABIT_KANALLAR:
        m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name}')
        m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
        m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
        m3u.append(f"{base_url}{file}")

    # 3. CANLI MAÇLARI EKLE
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    for stream_id, name in matches:
        clean_name = name.strip().upper()
        pure_id = stream_id.replace('betlivematch-', '')
        
        if pure_id.isdigit():
            link = f"{base_url}hls/{pure_id}.m3u8"
        else:
            link = f"{base_url}{pure_id}.m3u8"

        m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{clean_name}')
        m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
        m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
        m3u.append(link)

    # 4. KAYDET
    file_name = "joker.m3u8"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    print(f"🚀 Başarılı! {file_name} dosyası oluşturuldu.")

if __name__ == "__main__":
    main()
