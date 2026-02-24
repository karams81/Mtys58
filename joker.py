import re
import requests
import urllib3
import base64

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
TARGET_URL = "https://jokerbettv177.com/"
# Google üzerinden dolanarak Cloudflare'i kandırmaya çalışıyoruz
PROXY_URL = f"https://www.google.com/search?q={TARGET_URL}"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def get_html():
    # GitHub IP'si yerine bir proxy üzerinden istek atıyoruz
    # AllOrigins servisi genellikle bu tür engelleri aşmak için iyidir
    proxy_apis = [
        f"https://api.allorigins.win/get?url={TARGET_URL}",
        f"https://thingproxy.freeboard.io/fetch/{TARGET_URL}"
    ]
    
    for api in proxy_apis:
        try:
            print(f"🔄 Proxy deneniyor: {api[:40]}...")
            res = requests.get(api, headers={"User-Agent": UA}, timeout=25)
            
            if res.status_code == 200:
                # AllOrigins veriyi 'contents' anahtarı içinde döndürür
                if "allorigins" in api:
                    return res.json().get('contents', '')
                return res.text
        except Exception as e:
            print(f"⚠️ Proxy hatası: {e}")
            continue
            
    return None

def main():
    html = get_html()
    if not html or "data-stream" not in html:
        print("❌ Hiçbir proxy üzerinden içerik alınamadı.")
        return

    # Sunucu adresini (workers.dev) bul
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xsiic.workers.dev/"
    print(f"📡 Yayın Sunucusu Bulundu: {base_url}")

    m3u = ["#EXTM3U"]
    
    # 1. Canlı Maçları Ayıkla
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.IGNORECASE | re.DOTALL)
    
    for stream_id, name in matches:
        clean_name = name.strip().upper()
        pure_id = stream_id.replace('betlivematch-', '')
        link = f"{base_url}hls/{pure_id}.m3u8" if pure_id.isdigit() else f"{base_url}{pure_id}.m3u8"

        m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{clean_name}')
        m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
        m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
        m3u.append(link)

    with open("joker.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    print(f"🚀 Başarılı! {len(matches)} adet maç joker.m3u8 dosyasına eklendi.")

if __name__ == "__main__":
    main()
