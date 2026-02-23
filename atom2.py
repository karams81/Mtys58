import requests
import re
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
#  AtomSporTV  –  Canlı Maç + TV Kanalları M3U
# ─────────────────────────────────────────────
START_URL    = "https://url24.link/AtomSporTV"
MATCHES_URL  = "https://teletv3.top/load/matches.php"
LOGO_BASE    = "https://im.mackolik.com/img/logo/buyuk"
OUTPUT_FILE  = "atom_mac.m3u"

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://url24.link/'
}

# ── TV Kanalları ──────────────────────────────────────────────────────────────
TV_CHANNELS = [
    # (slug-id, Görünen Ad, logo_url)
    ("bein-sports-1", "BEIN SPORTS 1",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/BeIN_Sports_1_HD.svg/200px-BeIN_Sports_1_HD.svg.png"),
    ("bein-sports-2", "BEIN SPORTS 2",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/BeIN_Sports_2_HD.svg/200px-BeIN_Sports_2_HD.svg.png"),
    ("bein-sports-3", "BEIN SPORTS 3",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/BeIN_Sports_3_HD.svg/200px-BeIN_Sports_3_HD.svg.png"),
    ("bein-sports-4", "BEIN SPORTS 4",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/BeIN_Sports_4_HD.svg/200px-BeIN_Sports_4_HD.svg.png"),
    ("s-sport",       "S SPORT",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/S_Sport_logo.svg/200px-S_Sport_logo.svg.png"),
    ("s-sport-2",     "S SPORT 2",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/S_Sport_logo.svg/200px-S_Sport_logo.svg.png"),
    ("tivibu-spor-1", "TİVİBU SPOR 1", ""),
    ("tivibu-spor-2", "TİVİBU SPOR 2", ""),
    ("tivibu-spor-3", "TİVİBU SPOR 3", ""),
    ("trt-spor",      "TRT SPOR",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/TRT_Spor_logo.svg/200px-TRT_Spor_logo.svg.png"),
    ("trt-yildiz",    "TRT YILDIZ", ""),
    ("trt1",          "TRT 1",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/TRT_1_logo.svg/200px-TRT_1_logo.svg.png"),
    ("aspor",         "ASPOR",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/A_Spor_logo.svg/200px-A_Spor_logo.svg.png"),
]

# ─────────────────────────────────────────────────────────────────────────────

def get_base_domain():
    """Redirect zincirini takip ederek ana domain'i bul."""
    try:
        r1 = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in r1.headers:
            r2 = requests.get(r1.headers['location'], headers=headers,
                              allow_redirects=False, timeout=10)
            if 'location' in r2.headers:
                domain = r2.headers['location'].strip().rstrip('/')
                print(f"Ana Domain : {domain}")
                return domain
    except Exception as e:
        print(f"Domain hatası: {e}")
    return "https://atomsportv489.top"


def normalize_logo(src):
    """Göreli / protokolsüz logo URL'lerini tam URL'ye çevir."""
    if not src:
        return ""
    if src.startswith("http"):
        return src
    if src.startswith("//"):
        return "https:" + src
    # Göreceli yol → mackolik logo base'i
    return LOGO_BASE + "/" + src.lstrip("/")


def get_matches():
    """matches.php'den maç listesini parse et; takım logolarını da çek."""
    print(f"Maçlar çekiliyor → {MATCHES_URL}")
    try:
        resp = requests.get(MATCHES_URL, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        matches = []
        skip_words = {'futbol', 'futbol tr', 'futboi', 'günün maçı', 'futbol'}

        for a in soup.find_all('a', href=True):
            href = a['href']
            mid = re.search(r'matches\?id=([a-f0-9]+)', href)
            if not mid:
                continue
            match_id = mid.group(1)

            # Logolar
            imgs = a.find_all('img')
            home_logo = normalize_logo(imgs[0]['src']) if len(imgs) >= 1 else ""
            away_logo = normalize_logo(imgs[1]['src']) if len(imgs) >= 2 else ""
            logo = home_logo or away_logo

            # Metin
            lines = [l.strip() for l in a.get_text('\n').splitlines()
                     if l.strip() and l.strip().lower() not in skip_words]

            saat, lig, home_team, away_team = '', '', '', ''
            for line in lines:
                if '|' in line and not saat:
                    parts = line.split('|', 1)
                    saat = parts[0].strip()
                    lig  = parts[1].strip()
                elif saat and not home_team:
                    home_team = line
                elif saat and home_team and not away_team:
                    away_team = line

            home_team = home_team or "Ev Sahibi"
            away_team = away_team or "Deplasman"
            name = f"{saat} {home_team} - {away_team}"

            matches.append({
                'id'       : match_id,
                'name'     : name,
                'home'     : home_team,
                'away'     : away_team,
                'home_logo': home_logo,
                'away_logo': away_logo,
                'logo'     : logo,
                'time'     : saat,
                'league'   : lig,
                'group'    : lig if lig else 'Maçlar',
            })
            print(f"  ⚽ [{saat}] {home_team} vs {away_team}  (id={match_id[:8]}…)  logo={bool(logo)}")

        print(f"\nToplam {len(matches)} maç bulundu.")
        return matches

    except Exception as e:
        print(f"Maç çekme hatası: {e}")
        return []


def get_m3u8(resource_id, base_domain):
    """Verilen ID için m3u8 stream URL'sini çek."""
    try:
        h = headers.copy()
        h['Referer'] = base_domain

        resp = requests.get(f"{base_domain}/matches?id={resource_id}", headers=h, timeout=10)
        fetch_m = re.search(r'fetch\(\s*["\']([^"\']+)["\']', resp.text)
        if not fetch_m:
            return None

        fetch_url = fetch_m.group(1).strip()
        if not fetch_url.endswith(resource_id):
            fetch_url += resource_id

        h['Origin'] = base_domain
        resp2 = requests.get(fetch_url, headers=h, timeout=10)
        data  = resp2.text

        for pat in [
            r'"deismackanal":"(.*?)"',
            r'"stream":\s*"(.*?)"',
            r'"url":\s*"(.*?\.m3u8[^"]*)"',
            r'"source":\s*"(.*?\.m3u8[^"]*)"',
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
        ]:
            mm = re.search(pat, data)
            if mm:
                return mm.group(1).replace('\\/', '/').replace('\\', '')
        return None

    except Exception:
        return None


def test_items(items, base_domain):
    working = []
    for i, item in enumerate(items):
        print(f"  {i+1:2d}. {item['name']}...", end=" ", flush=True)
        url = get_m3u8(item['id'], base_domain)
        if url:
            print(f"{GREEN}✓{RESET}")
            item['url'] = url
            working.append(item)
        else:
            print("✗")
    return working


def extinf_line(item, group):
    """#EXTINF satırı yaz (logo varsa tvg-logo ekle)."""
    logo_attr = f' tvg-logo="{item["logo"]}"' if item.get("logo") else ''
    return (
        f'#EXTINF:-1 tvg-id="{item["id"]}" tvg-name="{item["name"]}"'
        f'{logo_attr} group-title="{group}",{item["name"]}\n'
    )


def build_m3u(working_matches, working_channels, base_domain):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        # ── Maçlar
        f.write("# ══════════════════════════════════\n")
        f.write("#  CANLI MAÇLAR\n")
        f.write("# ══════════════════════════════════\n\n")

        for m in working_matches:
            f.write(extinf_line(m, m['group']))
            if m.get('home_logo'):
                f.write(f'# logo-home: {m["home_logo"]}\n')
            if m.get('away_logo'):
                f.write(f'# logo-away: {m["away_logo"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(m['url'] + "\n\n")

        # ── TV Kanalları
        f.write("# ══════════════════════════════════\n")
        f.write("#  TV KANALLARI\n")
        f.write("# ══════════════════════════════════\n\n")

        for ch in working_channels:
            f.write(extinf_line(ch, "TV Kanalları"))
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(ch['url'] + "\n\n")

    print(f"\n{GREEN}[✓] {OUTPUT_FILE} oluşturuldu.{RESET}")
    print(f"    ⚽ Maç    : {len(working_matches)}")
    print(f"    📺 Kanal  : {len(working_channels)}")


# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{GREEN}AtomSporTV – Maç + TV Kanalları M3U Oluşturucu{RESET}")
    print("=" * 60)

    print("\n[1] Ana domain bulunuyor...")
    base_domain = get_base_domain()

    print("\n[2] Günün maçları çekiliyor...")
    matches = get_matches()

    print(f"\n[3] {len(matches)} maçın stream linki test ediliyor...")
    working_matches = test_items(matches, base_domain)

    print(f"\n[4] {len(TV_CHANNELS)} TV kanalı test ediliyor...")
    tv_items = [{'id': c[0], 'name': c[1], 'logo': c[2]} for c in TV_CHANNELS]
    working_channels = test_items(tv_items, base_domain)

    print("\n[5] M3U dosyası yazılıyor...")
    build_m3u(working_matches, working_channels, base_domain)

    print("\n" + "=" * 60)
    if working_matches:
        print(f"\n{YELLOW}⚽ ÇALIŞAN MAÇLAR:{RESET}")
        for m in working_matches:
            print(f"   ✓ {m['name']}")
    if working_channels:
        print(f"\n{YELLOW}📺 ÇALIŞAN TV KANALLARI:{RESET}")
        for ch in working_channels:
            print(f"   ✓ {ch['name']}")

    print("\n" + "=" * 60)
    print("GitHub:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "Günlük M3U güncelleme"')
    print("  git push")


if __name__ == "__main__":
    main()
