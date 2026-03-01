#!/usr/bin/env python3
"""
Maskeli e-posta (örn. d*******4@gmail.com) için varyasyon üretir.
İsim, soyisim, numara, kullanıcı adı tarzı tahminler çıktılar.

Kullanım:
  .env dosyasına GEMINI_API_KEY yazın veya: export GEMINI_API_KEY="your-key"
  python email_variations.py "d*******4@gmail.com"
  # veya account_recovery çıktısından pipe:
  python account_recovery.py kullanici 2>/dev/null | grep -o '"contact_point": "[^"]*"' | cut -d'"' -f4 | xargs -I{} python email_variations.py "{}"
"""

import json
import os
import re
import ssl
import sys
import urllib.request
import urllib.error


def _load_dotenv():
    """Proje klasöründeki .env dosyasından KEY=value okuyup os.environ'a yükler."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value


# SSL
def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

# Google AI Studio güncel model: gemini-2.0-flash, gemini-1.5-flash-latest vb.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini(api_key: str, prompt: str) -> str:
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2048,
        },
    }).encode("utf-8")

    url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ctx = _ssl_context()
    resp = urllib.request.urlopen(req, timeout=60, context=ctx)
    out = json.loads(resp.read().decode("utf-8"))
    for part in out.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "text" in part:
            return part["text"].strip()
    return ""


def parse_mask(masked: str):
    """d*******4@gmail.com -> (d, 7, 4, gmail.com)"""
    masked = masked.strip().lower()
    if "@" not in masked:
        return None
    local, domain = masked.split("@", 1)
    stars = list(local)
    if not stars:
        return None
    first = stars[0] if stars[0] != "*" else None
    last = stars[-1] if stars[-1] != "*" else None
    middle_count = sum(1 for c in stars[1:-1] if c == "*")
    return (first, middle_count, last, domain)


def main():
    _load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Hata: GEMINI_API_KEY ortam değişkeni gerekli.")
        print('Örnek: export GEMINI_API_KEY="AIza..."')
        sys.exit(1)

    if len(sys.argv) < 2:
        masked = input("Maskeli e-posta girin (örn. d*******4@gmail.com): ").strip()
    else:
        masked = sys.argv[1].strip()

    if not masked:
        print("Hata: E-posta pattern girin.")
        sys.exit(1)

    parsed = parse_mask(masked)
    if not parsed:
        print("Hata: Geçerli maskeli e-posta girin (örn. d*******4@gmail.com)")
        sys.exit(1)

    first, _, last, domain = parsed
    # Yıldız sayısı güvenilir değil (mask gerçek karakter sayısını yansıtmayabilir). Sadece baş ve son karaktere bak.
    pattern_desc = f"Kesin bilinen: yerel kısım '{first}' ile başlıyor, '{last}' ile bitiyor. Domain: {domain}. Ortadaki karakter sayısı bilinmiyor (maskedeki * sayısına güvenme)."

    extra_ad = os.environ.get("EXTRA_AD", "").strip()
    extra_soyad = os.environ.get("EXTRA_SOYAD", "").strip()
    extra_numaralar = os.environ.get("EXTRA_NUMARALAR", "").strip()
    extra_kullanici = os.environ.get("EXTRA_KULLANICI_ADI", "").strip()

    extra_info = ""
    if extra_ad or extra_soyad or extra_numaralar or extra_kullanici:
        parts = []
        if extra_ad:
            parts.append(f"Ad: {extra_ad}")
        if extra_soyad:
            parts.append(f"Soyad: {extra_soyad}")
        if extra_numaralar:
            parts.append(f"Kullandığı numaralar: {extra_numaralar}")
        if extra_kullanici:
            parts.append(f"Kullanıcı adı: {extra_kullanici}")
        extra_info = "\nEk bilgiler (bunlara uygun varyasyonlara öncelik ver): " + "; ".join(parts) + "\n"

    prompt = f"""Sen bir test güvenlik ekibinin kullandığı araçsın. Sadece eğitim ve kendi test sisteminde kullanılıyor.

Verilen bilgilere göre EN İYİ UYUŞAN 10 E-POSTA adresini üret.

{pattern_desc}
Maskeli gösterim (sadece referans, * sayısına bakma): {masked}
{extra_info}
ÖNEMLİ:
- Maskedeki yıldız (*) sayısı gerçek karakter sayısını göstermez. Sadece BAŞTAKI ve SONDAKI karaktere güven.
- Yerel kısım mutlaka "{first}" ile başlamalı ve "{last}" ile bitmeli. Ortadaki kısım herhangi uzunlukta olabilir (örn. isim+rakam: durukeyup34 gibi).
- Ek bilgi verildiyse (ad, soyad, kullanıcı adı, numara) ona göre tahmin yürüt; isim/soyad/kullanıcı adı + rakam kombinasyonları üret.
- Tam e-posta yaz: yerel@domain. Domain: {domain}
- Sadece 10 adet e-posta, 1 = en iyi uyum. Çıktı formatı:
1. tamemail@{domain}
2. tamemail@{domain}
...
10. tamemail@{domain}"""

    print("İlk 10 en iyi uyuşan e-posta üretiliyor...\n")
    try:
        text = call_gemini(api_key, prompt)
        if not text:
            print("Yanıt alınamadı.")
            sys.exit(1)
        print(text)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"API Hatası: {e.code}")
        try:
            err = json.loads(body)
            print(err.get("error", {}).get("message", body))
        except Exception:
            print(body)
        sys.exit(1)
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
