"""
LOGIN API FIX — Session memory leak tuzatish
/api/captcha-image va /api/connect-hemis DB orqali session qiladi
"""

# main.py ning login qismida quyidagi kodni almashtiramiz:

@app.get("/api/captcha-image")
async def api_captcha_image(telegram_id: int = 0):
    """
    Login sahifasini ochadi, captcha rasmini qaytaradi.
    Session'ni DB'da LoginSession'da saqlaydi (memory leak yok).
    """
    from bs4 import BeautifulSoup
    from database import LoginSession
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    
    base = "https://talaba.tsue.uz"
    login_url = base + "/dashboard/login"
    
    # Eski session'ni o'chiramiz
    async with AsyncSessionFactory() as db:
        await db.execute(delete(LoginSession).where(LoginSession.user_id == telegram_id))
        await db.commit()

    session = _make_session()
    try:
        # Login sahifasini yuklaymiz
        async with session.get(login_url, ssl=False) as r:
            html = await r.text()

        soup = BeautifulSoup(html, "html.parser")

        # CSRF token
        csrf_name, csrf_token = "_csrf-frontend", ""
        for inp in soup.find_all("input"):
            if "csrf" in inp.get("name", "").lower():
                csrf_name  = inp["name"]
                csrf_token = inp.get("value", "")
                break

        # Field nomlar
        username_field = "FormStudentLogin[login]"
        password_field = "FormStudentLogin[password]"
        captcha_field  = "FormStudentLogin[reCaptcha]"
        for inp in soup.find_all("input"):
            n, t = inp.get("name",""), inp.get("type","")
            if t in ("text","email") and n and "csrf" not in n.lower() and "captcha" not in n.lower():
                username_field = n
            if t == "password" and n:
                password_field = n
            if any(x in n.lower() for x in ["captcha","recaptcha","verifycode"]):
                captcha_field = n

        # Captcha rasmini yuklaymiz
        img_bytes = None
        for img in soup.find_all("img"):
            src = img.get("src","")
            if any(x in src.lower() for x in ["captcha","verify"]):
                img_url = (base + src) if src.startswith("/") else src
                async with session.get(img_url, ssl=False) as ir:
                    img_bytes = await ir.read()
                break

        if not img_bytes:
            await session.close()
            return {"image_b64": None, "field": ""}

        # Session'ni DB'da saqlayamiz (10 minut muddat)
        async with AsyncSessionFactory() as db:
            ls = LoginSession(
                user_id=telegram_id,
                csrf_token=csrf_token,
                username_field=username_field,
                password_field=password_field,
                captcha_field=captcha_field,
                expires_at=datetime.now() + timedelta(minutes=10),
            )
            db.add(ls)
            try:
                await db.commit()
            except:
                await db.rollback()

        # Session'ni yopamiz (u DB'da saqlanadi)
        await session.close()

        b64 = _b64.b64encode(img_bytes).decode()
        return {"image_b64": b64, "field": captcha_field}

    except Exception as e:
        await session.close()
        return {"image_b64": None, "field": "", "error": str(e)}


@app.post("/api/connect-hemis")
async def api_connect_hemis(body: HemisConnectRequest):
    """
    DB'da saqlangan session orqali login qiladi.
    Captcha va login bitta session'da bo'ladi.
    """
    from bs4 import BeautifulSoup
    from database import LoginSession
    from sqlalchemy import delete
    
    enc_pass = encrypt(body.password)

    # DB'dan session'ni olamiz
    async with AsyncSessionFactory() as db:
        from sqlalchemy import select
        res = await db.execute(
            select(LoginSession).where(LoginSession.user_id == body.telegram_id)
        )
        sess_row = res.scalars().first()
        
        if not sess_row:
            raise HTTPException(status_code=400, detail="Session muddati o'tgan. Captchani qayta yuklang.")
        
        if sess_row.expires_at < datetime.now():
            await db.execute(delete(LoginSession).where(LoginSession.user_id == body.telegram_id))
            await db.commit()
            raise HTTPException(status_code=400, detail="Session muddati o'tgan. Qayta boshlang.")
        
        csrf_name = "_csrf-frontend"
        csrf_token = sess_row.csrf_token
        username_field = sess_row.username_field
        password_field = sess_row.password_field
        captcha_field = sess_row.captcha_field
        
        # Session'ni o'chiramiz
        await db.execute(delete(LoginSession).where(LoginSession.user_id == body.telegram_id))
        await db.commit()

    # Login session yaratamiz
    session = _make_session()
    login_url = "https://talaba.tsue.uz/dashboard/login"
    
    try:
        from crypto import decrypt
        password = decrypt(enc_pass)

        form = {
            csrf_name: csrf_token,
            username_field: body.hemis_id,
            password_field: password,
            "FormStudentLogin[rememberMe]": "1",
            "FormStudentLogin[hasCaptcha]": "1",
            captcha_field: body.captcha_text,
        }

        session.headers.update({
            "Referer": login_url,
            "Origin": "https://talaba.tsue.uz",
        })

        async with session.post(login_url, data=form, allow_redirects=True, ssl=False) as r:
            final_url = str(r.url)
            body_text = await r.text()

        if "/dashboard/login" in final_url:
            soup = BeautifulSoup(body_text, "html.parser")
            err = soup.select_one(".alert-danger,.help-block,[class*='error'],[class*='danger']")
            msg = err.get_text(strip=True) if err else ""
            from scraper import HemisAuthError
            raise HemisAuthError(
                "Login muvaffaqiyatsiz!\n\n"
                + (f"Sabab: {msg}\n\n" if msg else "")
                + "Login yoki parolni tekshiring."
            )

        # Profil olish
        async with session.get("https://talaba.tsue.uz/dashboard/student-info", ssl=False) as r3:
            html3 = await r3.text()

        from scraper import _parse_profile
        profile = _parse_profile(html3)

    except Exception as e:
        await session.close()
        from scraper import HemisAuthError
        if isinstance(e, HemisAuthError):
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=503, detail=f"Hemis ga ulanib bo'lmadi: {e}")

    await session.close()

    # DB'ga saqlash
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == body.telegram_id))
        user = res.scalars().first()
        if not user:
            user = User(id=body.telegram_id)
            db.add(user)
            try:
                await db.flush()
            except:
                await db.rollback()
                res = await db.execute(select(User).where(User.id == body.telegram_id))
                user = res.scalars().first()

        user.hemis_id = body.hemis_id
        user.hemis_password_enc = enc_pass
        user.is_demo = False
        if profile.full_name and profile.full_name != "Noma'lum":
            user.full_name = profile.full_name
        user.last_login = datetime.now()
        await db.commit()

    return {
        "success": True,
        "profile": {
            "full_name": profile.full_name,
            "group": profile.group,
            "faculty": profile.faculty,
            "semester": profile.semester,
            "gpa": profile.gpa,
        }
    }
