import re
import cloudscraper
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar - Eğer 177 çalışmıyorsa burayı 178 veya güncel numara ile değiştirin
TARGET_URL = "https://jokerbettv177.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def get_html():
    # Daha gelişmiş bir scraper yapılandırması
    scraper = cloudscraper.create_scraper(
        delay=10, 
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        print(f"🔄 Bağlanıyor: {TARGET_URL}")
        # Bazı siteler doğrudan ana sayfaya bot engeli koyar, 
        # gerekirse bir alt sayfayı denemek gerekebilir.
        res = scraper.get(TARGET_URL, timeout=30)
        
        print(f"📡 Durum Kodu: {res.status_code}")
        
        if res.status_code == 200:
            return res.text
        elif res.status_code == 403:
            print("❌ Hata 403: Cloudflare hala engelliyor. IP adresiniz kara listede olabilir.")
        elif res.status_code == 404:
            print("❌ Hata 404: Site adresi (177) artık aktif değil. Yeni adrese geçilmiş.")
        else:
            print(f"❌ Beklenmedik hata: {res.status_code}")
            
    except Exception as e:
        print(f"❌ Kritik Bağlantı Hatası: {e}")
    return None

def main():
    html = get_html()
    if not html:
        print("🛑 Veri alınamadığı için işlem durduruldu.")
        return

    # Sunucu adresini (workers.dev) bul
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    
    if not base_match:
        print("⚠️ Sunucu adresi HTML içinde bulunamadı. Site yapısı değişmiş olabilir.")
        # Debug için HTML'in küçük bir kısmını yazdıralım
        print("HTML Başlangıcı:", html[:200])
        base_url = "https://pix.xsiic.workers.dev/"
    else:
        base_url = base_match.group(1)
        print(f"📡 Aktif Yayın Sunucusu: {base_url}")

    m3u = ["#EXTM3U"]
    # ... (Geri kalan m3u oluşturma kısımları aynı kalabilir)
    
    # 3. Canlı Maçları Ekle (Hata payını azaltmak için re.DOTALL ekli)
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.IGNORECASE | re.DOTALL)
    
    if not matches:
        print("⚠️ Canlı maç listesi bulunamadı.")
    else:
        for stream_id, name in matches:
            clean_name = name.strip().upper()
            pure_id = stream_id.replace('betlivematch-', '')
            link = f"{base_url}hls/{pure_id}.m3u8" if pure_id.isdigit() else f"{base_url}{pure_id}.m3u8"
            m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{clean_name}\n{link}')

    with open("joker.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    print("🚀 İşlem tamamlandı.")

if __name__ == "__main__":
    main()
