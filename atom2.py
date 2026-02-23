import requests
import re
from bs4 import BeautifulSoup

# AtomSporTV - Canlı Maç M3U Oluşturucu
START_URL = "https://url24.link/AtomSporTV"
MATCHES_URL = "https://teletv3.top/load/matches.php"
OUTPUT_FILE = "atom_mac.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://url24.link/'
}

def get_base_domain():
    """Ana domain'i bul (redirect takip ederek)"""
    try:
        response = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in response.headers:
            loc1 = response.headers['location']
            response2 = requests.get(loc1, headers=headers, allow_redirects=False, timeout=10)
            if 'location' in response2.headers:
                base_domain = response2.headers['location'].strip().rstrip('/')
                print(f"Ana Domain: {base_domain}")
                return base_domain
        return "https://atomsportv489.top"
    except Exception as e:
        print(f"Domain hatası: {e}")
        return "https://atomsportv489.top"

def get_matches():
    """matches.php'den bugünkü maçları çek"""
    print(f"Maçlar çekiliyor: {MATCHES_URL}")
    try:
        response = requests.get(MATCHES_URL, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        matches = []
        # Tüm <a> etiketlerini bul (her maç bir link)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # matches?id= içerenleri al
            match = re.search(r'matches\?id=([a-f0-9]+)', href)
            if not match:
                continue
            match_id = match.group(1)

            # Maç bilgilerini metinden çıkar
            text = a_tag.get_text(separator='\n', strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            # lines örneği: ['19:59 | Süper Lig', 'Fenerbahçe', 'Kasımpaşa']
            saat_lig = lines[0] if len(lines) > 0 else ''
            ev_sahibi = lines[1] if len(lines) > 1 else 'Ev Sahibi'
            deplasman = lines[2] if len(lines) > 2 else 'Deplasman'

            # Saat ve lig ayrıştır
            saat = ''
            lig = ''
            if '|' in saat_lig:
                parts = saat_lig.split('|', 1)
                saat = parts[0].strip()
                lig = parts[1].strip()
            else:
                saat = saat_lig

            kanal_adi = f"{saat} {ev_sahibi} - {deplasman}"

            matches.append({
                'id': match_id,
                'name': kanal_adi,
                'home': ev_sahibi,
                'away': deplasman,
                'time': saat,
                'league': lig,
                'group': lig if lig else 'Maçlar'
            })
            print(f"  Bulundu: [{saat}] {ev_sahibi} vs {deplasman} (id={match_id[:8]}...)")

        print(f"Toplam {len(matches)} maç bulundu.")
        return matches

    except Exception as e:
        print(f"Maç çekme hatası: {e}")
        return []

def get_match_m3u8(match_id, base_domain):
    """Maç ID'si ile m3u8 linkini çek"""
    try:
        matches_url = f"{base_domain}/matches?id={match_id}"
        custom_headers = headers.copy()
        custom_headers['Referer'] = base_domain

        response = requests.get(matches_url, headers=custom_headers, timeout=10)
        html = response.text

        # fetch URL'sini bul
        fetch_match = re.search(r'fetch\(\s*["\']([^"\']+)["\']', html)
        if not fetch_match:
            return None

        fetch_url = fetch_match.group(1).strip()

        # fetch URL'sine istek
        custom_headers['Origin'] = base_domain
        custom_headers['Referer'] = base_domain

        # ID'yi URL'ye ekle (gerekiryorsa)
        if not fetch_url.endswith(match_id):
            fetch_url_full = fetch_url + match_id
        else:
            fetch_url_full = fetch_url

        response2 = requests.get(fetch_url_full, headers=custom_headers, timeout=10)
        fetch_data = response2.text

        # m3u8 linkini bul
        patterns = [
            r'"deismackanal":"(.*?)"',
            r'"stream":\s*"(.*?)"',
            r'"url":\s*"(.*?\.m3u8[^"]*)"',
            r'"source":\s*"(.*?\.m3u8[^"]*)"',
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
        ]
        for pat in patterns:
            m = re.search(pat, fetch_data)
            if m:
                url = m.group(1).replace('\\/', '/').replace('\\', '')
                return url

        return None

    except Exception as e:
        return None

def test_matches(matches, base_domain):
    """Maçların stream linklerini çek"""
    print(f"\n{len(matches)} maç test ediliyor...")
    working = []

    for i, match in enumerate(matches):
        match_id = match['id']
        name = match['name']
        print(f"{i+1:2d}. {name}...", end=" ", flush=True)

        m3u8_url = get_match_m3u8(match_id, base_domain)

        if m3u8_url:
            print(f"{GREEN}✓{RESET}")
            match['url'] = m3u8_url
            working.append(match)
        else:
            print("✗")

    return working

def create_m3u(working_matches, base_domain):
    """M3U dosyası oluştur"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for match in working_matches:
            match_id = match['id']
            name = match['name']
            group = match.get('group', 'Maçlar')
            m3u8_url = match['url']

            f.write(f'#EXTINF:-1 tvg-id="{match_id}" tvg-name="{name}" group-title="{group}",{name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(m3u8_url + "\n")

    print(f"\n{GREEN}[✓] M3U oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {len(working_matches)} çalışan maç eklendi.")

def main():
    print(f"{GREEN}AtomSporTV - Canlı Maç M3U Oluşturucu{RESET}")
    print("=" * 60)

    # 1. Domain bul
    print("\n1. Ana domain bulunuyor...")
    base_domain = get_base_domain()

    # 2. Maçları çek
    print("\n2. Günün maçları çekiliyor...")
    matches = get_matches()

    if not matches:
        print("❌ Hiç maç bulunamadı!")
        return

    # 3. Stream linklerini çek
    print("\n3. Stream linkleri çekiliyor...")
    working = test_matches(matches, base_domain)

    if not working:
        print("\n❌ Hiç çalışan stream bulunamadı!")
        return

    # 4. M3U oluştur
    print("\n4. M3U dosyası oluşturuluyor...")
    create_m3u(working, base_domain)

    # 5. Sonuçlar
    print("\n" + "=" * 60)
    print("ÇALIŞAN MAÇLAR:")
    for m in working:
        print(f"  ✓ {m['name']}")

    print("\n" + "=" * 60)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "Günlük maç M3U güncellemesi"')
    print("  git push")

if __name__ == "__main__":
    main()
