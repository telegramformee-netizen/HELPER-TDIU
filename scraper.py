"""
scraper.py — TSUE talaba.tsue.uz Hemis scraper
Login forma aniqlab olingan versiya.
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
import hashlib, re, json
import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "uz-UZ,uz;q=0.9,ru;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
}

LESSON_TIMES = {
    1: ("08:30","09:50"), 2: ("10:00","11:20"),
    3: ("11:30","12:50"), 4: ("13:30","14:50"),
    5: ("15:00","16:20"), 6: ("16:30","17:50"),
    7: ("18:00","19:20"), 8: ("20:00","21:20"),
}


@dataclass
class HemisGrade:
    subject: str
    hemis_id: str
    current: Optional[float]
    midterm: Optional[float]
    final:   Optional[float]
    total:   Optional[float]
    total_hours: Optional[int]
    missed: Optional[int]
    semester: str

@dataclass
class HemisLesson:
    date: str
    weekday: int
    num: int
    start: str
    end: str
    subject: str
    s_type: str
    teacher: str
    room: str
    building: str
    hash: str = field(init=False)

    def __post_init__(self):
        raw = f"{self.date}{self.num}{self.subject}{self.room}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:12]

@dataclass
class HemisProfile:
    full_name: str
    student_id: str
    group: str
    faculty: str
    semester: str
    gpa: Optional[float]
    level: str = ""
    study_form: str = ""

class HemisAuthError(Exception): pass
class HemisError(Exception): pass


class HemisScraper:
    def __init__(self, user_id, hemis_id, enc_password,
                 demo=False, cookies=None):
        self.user_id   = user_id
        self.hemis_id  = hemis_id
        self._enc_pass = enc_password
        self.demo      = demo
        self._cookies  = cookies or {}
        self._session  = None
        self._base     = config.HEMIS_BASE_URL.rstrip("/")

    async def __aenter__(self):
        # ssl=False — ba'zi serverlar self-signed sertifikat ishlatadi
        connector = aiohttp.TCPConnector(ssl=False)
        timeout   = aiohttp.ClientTimeout(total=30, connect=10)
        jar       = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(
            headers=HEADERS,
            timeout=timeout,
            connector=connector,
            cookie_jar=jar,
        )
        if self._cookies:
            self._session.cookie_jar.update_cookies(self._cookies)
        return self

    async def __aexit__(self, *_):
        if self._session:
            await self._session.close()

    async def ensure_login(self):
        if self.demo: return
        if await self._valid(): return
        await self._login()

    async def get_cookies_dict(self) -> dict:
        return {c.key: c.value for c in self._session.cookie_jar}

    async def fetch_profile(self) -> HemisProfile:
        if self.demo: return _demo_profile()
        html = await self._get("/dashboard/student-info")
        return _parse_profile(html)

    async def fetch_grades(self, semester_id: str = "") -> list:
        if self.demo: return _demo_grades()
        path = "/student/performance"
        if semester_id:
            path += f"?_semester_id={semester_id}"
        html = await self._get(path)
        return _parse_grades(html)

    async def fetch_semesters(self) -> list:
        if self.demo:
            return [
                {"id":"162","label":"2024-2025 (2-semestr)","active":True},
                {"id":"161","label":"2024-2025 (1-semestr)","active":False},
                {"id":"160","label":"2023-2024 (2-semestr)","active":False},
            ]
        html = await self._get("/student/performance")
        return _parse_semesters(html)

    async def fetch_schedule(self, target: Optional[date] = None) -> list:
        if self.demo: return _demo_schedule(target or date.today())
        td     = target or date.today()
        monday = td - timedelta(days=td.weekday())
        html   = await self._get(f"/student/time-table?week={monday.isoformat()}")
        return _parse_schedule(html, monday)

    async def fetch_raw_html(self, path: str) -> str:
        if self.demo: return "<p>Demo mode</p>"
        return await self._get(path)

    async def inspect_login_form(self) -> dict:
        """
        Login sahifasining forma tuzilmasini qaytaradi.
        Debug uchun.
        """
        try:
            async with self._session.get(
                self._base + "/dashboard/login"
            ) as r:
                html = await r.text()
            soup  = BeautifulSoup(html, "html.parser")
            forms = []
            for form in soup.find_all("form"):
                inputs = []
                for inp in form.find_all(["input","button"]):
                    inputs.append({
                        "tag":   inp.name,
                        "name":  inp.get("name",""),
                        "type":  inp.get("type",""),
                        "value": inp.get("value","")[:30] if inp.get("value") else "",
                        "id":    inp.get("id",""),
                    })
                forms.append({
                    "action": form.get("action",""),
                    "method": form.get("method",""),
                    "inputs": inputs,
                })
            return {
                "url": self._base + "/dashboard/login",
                "forms": forms,
                "html_snippet": html[:2000],
            }
        except Exception as e:
            return {"error": str(e)}

    # ── Internal ──────────────────────────────────────────────

    async def _valid(self) -> bool:
        if not self._cookies: return False
        try:
            async with self._session.get(
                self._base + "/dashboard",
                allow_redirects=False,
            ) as r:
                loc = r.headers.get("Location","")
                return r.status == 200 or (r.status in (301,302) and "login" not in loc)
        except:
            return False

    async def _login(self):
        from crypto import decrypt
        password = decrypt(self._enc_pass)

        # ── Qadam 1: Login sahifasini yuklaymiz ──────────────────
        login_url = self._base + "/dashboard/login"
        async with self._session.get(login_url) as r:
            html = await r.text()

        soup = BeautifulSoup(html, "html.parser")

        # ── Qadam 2: Barcha inputlarni topamiz ──────────────────
        # CSRF token — turli nomlar bilan kelishi mumkin
        csrf_name  = "_csrf-frontend"
        csrf_token = ""

        for inp in soup.find_all("input", {"type": ["hidden", ""]}):
            name = inp.get("name", "")
            val  = inp.get("value", "")
            if "csrf" in name.lower():
                csrf_name  = name
                csrf_token = val
                break

        # ── Qadam 3: Username va password field nomlarini topamiz ─
        username_field = "LoginForm[username]"
        password_field = "LoginForm[password]"
        remember_field = "LoginForm[rememberMe]"

        for inp in soup.find_all("input"):
            inp_name = inp.get("name","")
            inp_type = inp.get("type","")
            inp_id   = inp.get("id","").lower()

            if inp_type == "text" or "username" in inp_id or "login" in inp_id:
                if inp_name and "csrf" not in inp_name.lower():
                    username_field = inp_name

            if inp_type == "password":
                if inp_name:
                    password_field = inp_name

        # ── Qadam 4: Login so'rovini yuboramiz ───────────────────
        form_data = {
            username_field: self.hemis_id,
            password_field: password,
        }
        if csrf_token:
            form_data[csrf_name] = csrf_token

        # rememberMe qo'shamiz
        for inp in soup.find_all("input", {"type": "checkbox"}):
            name = inp.get("name","")
            if "remember" in name.lower() or "remember" in inp.get("id","").lower():
                form_data[name] = inp.get("value","1")
                break
        else:
            if remember_field not in form_data:
                form_data[remember_field] = "1"

        async with self._session.post(
            login_url,
            data=form_data,
            allow_redirects=True,
        ) as r:
            final_url = str(r.url)
            body      = await r.text()

        # ── Qadam 5: Login natijasini tekshiramiz ────────────────
        if "/dashboard/login" in final_url:
            # Xato xabarini topamiz
            err_soup = BeautifulSoup(body, "html.parser")
            err_el   = err_soup.select_one(
                ".alert-danger, .help-block, .error, "
                "[class*='error'], [class*='danger']"
            )
            err_msg = err_el.get_text(strip=True) if err_el else ""

            raise HemisAuthError(
                "Login muvaffaqiyatsiz!\n\n"
                + (f"Sabab: {err_msg}\n\n" if err_msg else "")
                + "talaba.tsue.uz dagi login va parolingizni kiriting.\n"
                "Login — o'quvchilik ID raqamingiz (masalan: 123456789)"
            )

    async def _get(self, path: str, attempt: int = 1) -> str:
        url = self._base + path
        try:
            async with self._session.get(url, allow_redirects=True) as r:
                if "/dashboard/login" in str(r.url) and attempt == 1:
                    await self._login()
                    return await self._get(path, attempt=2)
                r.raise_for_status()
                return await r.text()
        except aiohttp.ClientResponseError as e:
            raise HemisError(f"HTTP {e.status}: {path}")
        except aiohttp.ClientError as e:
            if attempt < 3:
                await asyncio.sleep(2 ** attempt)
                return await self._get(path, attempt + 1)
            raise HemisError(f"Ulanib bo'lmadi: {e}")


# ══════════════════════════════════════════════════════════
# PARSERS
# ══════════════════════════════════════════════════════════

def _parse_profile(html: str) -> HemisProfile:
    s = BeautifulSoup(html, "html.parser")
    info = {}

    for row in s.select("table tr"):
        cells = row.find_all(["td","th"])
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower()
            val = cells[1].get_text(strip=True)
            info[key] = val

    def fv(*keys):
        for k in keys:
            for ik, iv in info.items():
                if any(x in ik for x in k.split("|")):
                    return iv
        return ""

    full_name  = fv("f.i.sh|ф.и.о|ism|fish|fio|ismi")
    group      = fv("guruh|группа|group")
    faculty    = fv("fakultet|факультет|faculty")
    semester   = fv("semestr|семестр")
    student_id = fv("hemis id|talaba id|student id|рaqam")
    level      = fv("daraja|степень|level|ta'lim turi")

    if not full_name:
        for sel in ["h4","h3",".student-name",".profile-name","[class*='name']"]:
            el = s.select_one(sel)
            if el:
                full_name = el.get_text(strip=True)
                break

    gpa = None
    for el in s.select("td,.gpa"):
        t = el.get_text(strip=True)
        if re.match(r"^\d\.\d{1,2}$", t):
            v = float(t)
            if 0 < v <= 5:
                gpa = v
                break

    return HemisProfile(
        full_name=full_name or "Noma'lum",
        student_id=student_id,
        group=group, faculty=faculty,
        semester=semester, gpa=gpa, level=level,
    )


def _parse_semesters(html: str) -> list:
    s = BeautifulSoup(html, "html.parser")
    result = []
    for sel_el in s.find_all("select"):
        if "semester" in sel_el.get("name","").lower():
            for opt in sel_el.find_all("option"):
                val = opt.get("value","")
                lbl = opt.get_text(strip=True)
                sel = opt.get("selected") is not None
                if val and val != "0":
                    result.append({"id":val,"label":lbl,"active":sel})
            break
    return result


def _parse_grades(html: str) -> list:
    s = BeautifulSoup(html, "html.parser")
    result = []

    table = (
        s.find("table", class_="table") or
        s.find("table", class_=re.compile("table")) or
        s.find("table")
    )
    if not table:
        return _demo_grades()

    for row in table.select("tbody tr"):
        cols  = row.find_all("td")
        if len(cols) < 4: continue
        texts = [c.get_text(strip=True) for c in cols]

        subject = texts[1] if len(texts) > 1 else texts[0]
        if not subject or len(subject) < 3 or subject.isdigit():
            continue

        cur = _f(texts[2]) if len(texts) > 2 else None
        mid = _f(texts[3]) if len(texts) > 3 else None
        fin = _f(texts[4]) if len(texts) > 4 else None
        tot = _f(texts[5]) if len(texts) > 5 else None
        hrs = _i(texts[6]) if len(texts) > 6 else None
        ms  = _i(texts[7]) if len(texts) > 7 else None

        if cur is not None and cur > 20: cur = None
        if mid is not None and mid > 30: mid = None
        if fin is not None and fin > 50: fin = None
        if tot is None:
            tot = (cur or 0) + (mid or 0) + (fin or 0)

        result.append(HemisGrade(
            subject=_cl(subject), hemis_id=texts[0],
            current=cur, midterm=mid, final=fin, total=tot,
            total_hours=hrs, missed=ms, semester=_sem(),
        ))

    return result if result else _demo_grades()


def _parse_schedule(html: str, week_start: date) -> list:
    s = BeautifulSoup(html, "html.parser")
    lessons = []

    # Usul 1: Haftalik jadval table
    table = (
        s.find("table", class_=re.compile(r"schedule|timetable|jadval", re.I)) or
        s.find("table")
    )
    if table:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all(["td","th"])
            if not cols: continue
            num = _i(cols[0].get_text(strip=True)) or 1
            for ci, cell in enumerate(cols[1:7]):
                text = cell.get_text(" ", strip=True)
                if not text or len(text) < 3: continue
                d = week_start + timedelta(days=ci)
                st, en = LESSON_TIMES.get(num, ("00:00","00:00"))
                lessons.append(HemisLesson(
                    date=d.isoformat(), weekday=d.weekday(), num=num,
                    start=st, end=en, subject=_cl(text[:80]),
                    s_type="", teacher="", room="", building="",
                ))

    # Usul 2: Kunlar bo'yicha divlar
    if not lessons:
        for di, day_el in enumerate(s.select(".schedule-day,.timetable-day")):
            d = week_start + timedelta(days=di)
            for cell in day_el.select(".lesson-cell,.lesson,tr"):
                num = _i(_txt(cell, ".num")) or 1
                subj = _txt(cell, ".subject,strong,b")
                if not subj: continue
                st, en = LESSON_TIMES.get(num, ("00:00","00:00"))
                lessons.append(HemisLesson(
                    date=d.isoformat(), weekday=d.weekday(), num=num,
                    start=st, end=en, subject=_cl(subj),
                    s_type =_cl(_txt(cell,".type")),
                    teacher=_cl(_txt(cell,".teacher")),
                    room   =_cl(_txt(cell,".room,.auditoriya")),
                    building="",
                ))

    return sorted(lessons, key=lambda l: (l.date, l.num))


def _txt(el, selector: str) -> str:
    found = el.select_one(selector)
    return found.get_text(strip=True) if found else ""

def _cl(t: str) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip()

def _f(t) -> Optional[float]:
    if t is None: return None
    m = re.search(r"\d+\.?\d*", str(t).replace(",",".").strip())
    return float(m.group()) if m else None

def _i(t) -> Optional[int]:
    if t is None: return None
    m = re.search(r"\d+", str(t))
    return int(m.group()) if m else None

def _sem() -> str:
    from datetime import datetime
    n = datetime.now()
    return f"{n.year}-{1 if n.month<=6 else 2}"


# ── Demo Data ─────────────────────────────────────────────

def _demo_profile():
    return HemisProfile(
        "Demo Talaba","U2200000","IQ-22-01",
        "Iqtisodiyot","2024-2025 (2-semestr)",3.45,"Bakalavr","Kunduzgi"
    )

def _demo_grades():
    data = [
        ("Mikroiqtisodiyot","1",17,24,None,41,64,4),
        ("Bank ishi va kredit","2",15,22,None,37,72,6),
        ("Iqtisodiy siyosat","3",18,28,None,46,80,2),
        ("Pul va kredit","4",12,18,None,30,64,14),
        ("Marketing asoslari","5",19,26,None,45,72,0),
        ("Tadbirkorlik asoslari","6",16,25,None,41,56,6),
    ]
    return [HemisGrade(s,h,c,m,f,t,hr,ms,"2024-2") for s,h,c,m,f,t,hr,ms in data]

def _demo_schedule(target):
    monday = target - timedelta(days=target.weekday())
    items = [
        (0,1,"Mikroiqtisodiyot","Ma'ruza","Salimov B.","A-301","A blok"),
        (0,3,"Bank ishi","Seminar","Rahimov N.","B-204","B blok"),
        (1,2,"Pul va kredit","Ma'ruza","Hasanov M.","A-101","A blok"),
        (2,1,"Iqtisodiy siyosat","Ma'ruza","Toshmatov A.","A-201","A blok"),
        (3,2,"Mikroiqtisodiyot","Seminar","Salimov B.","B-102","B blok"),
        (4,3,"Bank ishi","Ma'ruza","Rahimov N.","A-301","A blok"),
    ]
    result = []
    for di,num,subj,stype,teacher,room,building in items:
        d = monday + timedelta(days=di)
        st,en = LESSON_TIMES[num]
        result.append(HemisLesson(d.isoformat(),d.weekday(),num,st,en,subj,stype,teacher,room,building))
    return sorted(result, key=lambda l:(l.date,l.num))
