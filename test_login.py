"""
test_login.py — talaba.tsue.uz login sinov scripti
Ishlatish: python3 test_login.py

Bu script Railway serverida ham ishlaydi:
  railway run python3 test_login.py
"""

import requests
from bs4 import BeautifulSoup

# ── Sozlamalar ─────────────────────────────────────────────────
BASE_URL   = "https://talaba.tsue.uz"
LOGIN_URL  = BASE_URL + "/dashboard/login"
HEMIS_ID   = "324241104710"   # <-- o'zingiznikini kiriting
PASSWORD   = "24052007ulugbek"  # <-- o'zingiznikini kiriting

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "uz-UZ,uz;q=0.9,ru;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
}

# ── Proxy sozlamasi (kerak bo'lsa) ─────────────────────────────
# Railway xorijiy IP ishlatadi. Agar talaba.tsue.uz blok qilsa:
# 1. O'zbek proxy sotib oling (masalan: brightdata.com yoki proxy6.net)
# 2. Quyidagi PROXY ni to'ldiring:
PROXY = None  # yoki: "http://user:pass@proxy-host:port"

proxies = {"http": PROXY, "https": PROXY} if PROXY else None


def test_login():
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False  # SSL sertifikat tekshirishni o'chiramiz

    import urllib3
    urllib3.disable_warnings()  # SSL ogohlantirishlarni yashiramiz

    print("=" * 55)
    print("1. Login sahifasiga GET so'rov yuborilmoqda...")
    print(f"   URL: {LOGIN_URL}")

    try:
        r = session.get(LOGIN_URL, proxies=proxies, timeout=20)
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ULANISH XATOSI: {e}")
        print("\n🔍 Sabab taxmini:")
        if "Connection reset" in str(e) or "Connection refused" in str(e):
            print("   → talaba.tsue.uz Railway IP sini BLOKLAYAPTI!")
            print("   → Yechim: O'zbek proxy ulash kerak (quyida ko'rsatilgan)")
        elif "Name or service not known" in str(e):
            print("   → DNS xatosi — internet aloqasi yo'q")
        print_proxy_guide()
        return
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT — server javob bermadi (20 sek)")
        print_proxy_guide()
        return

    print(f"   Status: {r.status_code}")
    print(f"   Cookie'lar: {dict(session.cookies)}")

    if r.status_code == 403:
        print("\n❌ 403 FORBIDDEN — IP manzil bloklangan!")
        print_proxy_guide()
        return

    if r.status_code != 200:
        print(f"\n❌ Kutilmagan status: {r.status_code}")
        return

    print("   ✅ Sahifa yuklandi")

    # ── HTML tahlil ────────────────────────────────────────────
    soup = BeautifulSoup(r.text, "html.parser")

    # CSRF tokenni topamiz
    csrf_name, csrf_value = None, None
    for inp in soup.find_all("input"):
        name = inp.get("name", "")
        if "csrf" in name.lower():
            csrf_name  = name
            csrf_value = inp.get("value", "")
            break

    # Username/password field nomlarini topamiz
    username_field = "LoginForm[username]"
    password_field = "LoginForm[password]"
    captcha_field  = None

    for inp in soup.find_all("input"):
        n = inp.get("name", "")
        t = inp.get("type", "")
        i = inp.get("id", "").lower()
        if t in ("text", "email") or "username" in i or "login" in i:
            if n and "csrf" not in n.lower() and "captcha" not in n.lower():
                username_field = n
        if t == "password" and n:
            password_field = n
        if any(x in n.lower() for x in ["captcha", "verifycode", "recaptcha"]):
            captcha_field = n

    print(f"\n2. Form tahlil natijasi:")
    print(f"   CSRF field : {csrf_name} = {csrf_value[:20] if csrf_value else 'YOQ'}...")
    print(f"   Username   : {username_field}")
    print(f"   Password   : {password_field}")
    print(f"   Captcha    : {captcha_field or 'YOQ'}")

    # Captcha bor bo'lsa — rasmni yuklaymiz va ko'rsatamiz
    captcha_text = ""
    if captcha_field:
        print(f"\n   ⚠️  CAPTCHA topildi: {captcha_field}")
        # Captcha rasmini topamiz
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if any(x in src.lower() for x in ["captcha", "verify"]):
                img_url = BASE_URL + src if src.startswith("/") else src
                print(f"   Captcha URL: {img_url}")
                try:
                    ir = session.get(img_url, proxies=proxies, timeout=10)
                    with open("/tmp/captcha.png", "wb") as f:
                        f.write(ir.content)
                    print("   Captcha rasmi /tmp/captcha.png ga saqlandi")
                    print("   ➡ Captcha matnini kiriting:")
                    captcha_text = input("   > ").strip()
                except Exception as e:
                    print(f"   Captcha yuklanmadi: {e}")
                break

    # ── POST so'rov ────────────────────────────────────────────
    print(f"\n3. Login POST so'rovi yuborilmoqda...")

    form_data = {
        username_field:        HEMIS_ID,
        password_field:        PASSWORD,
        "LoginForm[rememberMe]": "1",
    }
    if csrf_name and csrf_value:
        form_data[csrf_name] = csrf_value
    if captcha_field and captcha_text:
        form_data[captcha_field] = captcha_text

    print(f"   Form data: {list(form_data.keys())}")

    # Referer header qo'shamiz (brauzer kabi)
    session.headers["Referer"] = LOGIN_URL
    session.headers["Origin"]  = BASE_URL

    r2 = session.post(
        LOGIN_URL,
        data=form_data,
        proxies=proxies,
        timeout=20,
        allow_redirects=True,
    )

    print(f"   Status: {r2.status_code}")
    print(f"   Final URL: {r2.url}")

    if "/dashboard/login" in str(r2.url):
        soup2 = BeautifulSoup(r2.text, "html.parser")
        err = soup2.select_one(".alert-danger, .help-block, [class*='error']")
        err_msg = err.get_text(strip=True) if err else "Noma'lum xato"
        print(f"\n❌ LOGIN MUVAFFAQIYATSIZ!")
        print(f"   Xato: {err_msg}")
        return

    print(f"\n✅ LOGIN MUVAFFAQIYATLI!")
    print(f"   Cookie'lar: {dict(session.cookies)}")

    # ── Dashboard dan ma'lumot olish ──────────────────────────
    print(f"\n4. Dashboard ma'lumotlari yuklanmoqda...")
    r3 = session.get(
        BASE_URL + "/dashboard/student-info",
        proxies=proxies,
        timeout=20,
    )
    soup3 = BeautifulSoup(r3.text, "html.parser")

    # Ismni topamiz
    name = ""
    for sel in ["h4", "h3", ".student-name", "[class*='name']"]:
        el = soup3.select_one(sel)
        if el:
            name = el.get_text(strip=True)
            break

    print(f"   Talaba ismi: {name or 'Topilmadi'}")
    print("\n🎉 Scraper to'g'ri ishlayapti!")


def print_proxy_guide():
    print("\n" + "=" * 55)
    print("📋 PROXY ULASH YO'RIQNOMASI:")
    print("=" * 55)
    print("""
1. O'zbek yoki Markaziy Osiyo proksi sotib oling:
   - https://proxy6.net  (arzon, soatlik to'lov)
   - https://brightdata.com
   - https://proxyscrape.com

2. test_login.py dagi PROXY ni to'ldiring:
   PROXY = "http://username:password@proxy-host:3128"

3. Railway da ham proxy ishlatish uchun main.py scraper ga:
   connector = aiohttp.TCPConnector(ssl=False)
   # va barcha so'rovlarga proxy= parametr qo'shing

4. Muqobil yechim — Railway o'rniga O'zbekistondagi
   hosting ishlatish (reg.uz, uztelecom.uz VPS ~$5/oy)
""")
    print("=" * 55)


if __name__ == "__main__":
    test_login()
