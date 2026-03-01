#!/usr/bin/env python3
"""
Hesap kurtarma (şifremi unuttum) - Terminal otomasyonu.
Kullanım: python account_recovery.py <kullanici_adi_veya_email>
requests gerekmez, sadece Python stdlib kullanır.
"""

import json
import ssl
import sys
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

# SSL: macOS'ta sertifika hatası için certifi kullan veya doğrulamayı kapat
def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        print("Uyarı: SSL doğrulama atlandı (certifi yok). Sadece test için kullanın.")
        return ctx

BASE = "https://www.instagram.com"
RECOVERY_URL = f"{BASE}/api/v1/web/accounts/account_recovery_send_ajax/"
RESET_PAGE = f"{BASE}/accounts/password/reset/"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python account_recovery.py <kullanici_adi_veya_email>")
        print("Örnek:    python account_recovery.py eyupd0")
        sys.exit(1)

    email_or_username = sys.argv[1].strip()
    if not email_or_username:
        print("Hata: Kullanıcı adı veya e-posta boş olamaz.")
        sys.exit(1)

    # Cookie'leri saklamak için; SSL bağlamı
    cookie_jar = CookieJar()
    ssl_ctx = _ssl_context()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=ssl_ctx),
    )

    try:
        # 1) Önce anasayfaya GET at, cookie ve CSRF al
        print("Anasayfa açılıyor, CSRF token alınıyor...")
        req = urllib.request.Request(
            "https://www.instagram.com/",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            },
            method="GET",
        )
        r = opener.open(req, timeout=15)
        r.read()

        csrf = None
        for c in cookie_jar:
            if c.name == "csrftoken":
                csrf = c.value
                break

        if not csrf:
            print("Uyarı: csrftoken cookie bulunamadı, yine de denenecek.")

        # 2) Hesap kurtarma isteği gönder
        body = urllib.parse.urlencode({
            "email_or_username": email_or_username,
            "jazoest": "23004",
        }).encode("utf-8")

        post_headers = {
            "User-Agent": USER_AGENT,
            "Referer": RESET_PAGE,
            "Origin": BASE,
            "X-Requested-With": "XMLHttpRequest",
            "X-Ig-App-Id": "936619743392459",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
        }
        if csrf:
            post_headers["X-Csrftoken"] = csrf
            post_headers["X-CSRFToken"] = csrf

        print(f"Hesap kurtarma isteği gönderiliyor: {email_or_username}")
        req2 = urllib.request.Request(
            RECOVERY_URL,
            data=body,
            headers=post_headers,
            method="POST",
        )
        resp = opener.open(req2, timeout=15)
        status = resp.getcode()
        raw = resp.read().decode("utf-8", errors="replace")

        print(f"\nDurum kodu: {status}")
        print("Yanıt:")

        try:
            js = json.loads(raw)
            for key in ("title", "body"):
                js.pop(key, None)
            print(json.dumps(js, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(raw)

    except urllib.error.HTTPError as e:
        print(f"\nHTTP Hata: {e.code} {e.reason}")
        try:
            body = e.read().decode("utf-8", errors="replace")
            try:
                js = json.loads(body)
                for key in ("title", "body"):
                    js.pop(key, None)
                print(json.dumps(js, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(body)
        except Exception:
            pass
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Hata (ağ): {e.reason}")
        sys.exit(1)
    except OSError as e:
        print(f"Hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
