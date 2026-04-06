"""
scraper.py — TSUE (talaba.tsue.uz) Hemis scraper
Standart Hemis tizimiga moslashtirilgan selektorlar.
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
}

# TSUE Hemis dars vaqtlari
LESSON_TIMES = {
    1: ("08:30", "09:50"),
    2: ("10:00", "11:20"),
    3: ("11:30", "12:50"),
    4: ("13:30", "14:50"),
    5: ("15:00", "16:20"),
    6: ("16:30", "17:50"),
    7: ("18:00", "19:20"),
    8: ("20:00", "21:20"),
}


@dataclass
class HemisGrade:
    subject: str
    hemis_id: str
    current: Optional[float]    # max 20
    midterm: Optional[float]    # max 30
    final:   Optional[float]    # max 50
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
        connector = aiohttp.TCPConnector(ssl=False)
        timeout   = aiohttp.ClientTimeout(total=30, connect=10)
        self._session = aiohttp.ClientSession(
            headers=HEADERS,
            timeout=timeout,
            connector=connector,
        )
        if self._cookies:
            self._session.cookie_jar.update_cookies(self._cookies)
        return self

    async def __aexit__(self, *_):
        if self._session:
            await self._session.close()

    # ── Public ────────────────────────────────────────────────

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
                {"id": "162", "label": "2024-2025 (2-semestr)", "active": True},
                {"id": "161", "label": "2024-2025 (1-semestr)", "active": False},
                {"id": "160", "label": "2023-2024 (2-semestr)", "active": False},
                {"id": "159", "label": "2023-2024 (1-semestr)", "active": False},
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

    # ── Internal ──────────────────────────────────────────────

    async def _valid(self) -> bool:
        if not self._cookies: return False
        try:
            async with self._session.get(
                self._base + "/dashboard",
                allow_redirects=False
            ) as r:
                return r.status == 200
        except: return False

    async def _login(self):
        from crypto import decrypt
        password = decrypt(self._enc_pass)

        # 1. Login sahifasini olamiz
        async with self._session.get(
            self._base + "/dashboard/login"
        ) as r:
            html = await r.text()

        soup = BeautifulSoup(html, "html.parser")

        # CSRF token
        csrf_input = soup.find("input", {"name": "_csrf-frontend"})
        if not csrf_input:
            csrf_input = soup.find("input", {"name": re.compile(r"csrf", re.I)})
        csrf_token = csrf_input.get("value", "") if csrf_input else ""
        csrf_name  = csrf_input.get("name", "_csrf-frontend") if csrf_input else "_csrf-frontend"

        # 2. Login so'rovini yuboramiz
        async with self._session.post(
            self._base + "/dashboard/login",
            data={
                csrf_name: csrf_token,
                "LoginForm[username]": self.hemis_id,
                "LoginForm[password]": password,
                "LoginForm[rememberMe]": "1",
            },
            allow_redirects=True,
        ) as r:
            final_url = str(r.url)
            body      = await r.text()

        # Login sahifasiga qaytdik → credentials noto'g'ri
        if "/dashboard/login" in final_url:
            raise HemisAuthError(
                "Login ID yoki parol noto'g'ri!\n"
                "talaba.tsue.uz dagi login va parolingizni kiriting."
            )

        # Xato xabari bor-yo'qligini tekshiramiz
        if "has-error" in body or "alert-danger" in body:
            soup2 = BeautifulSoup(body, "html.parser")
            err   = soup2.select_one(".alert-danger, .help-block")
            msg   = err.get_text(strip=True) if err else "Login muvaffaqiyatsiz"
            raise HemisAuthError(msg)

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
# PARSERS — TSUE talaba.tsue.uz uchun
# ══════════════════════════════════════════════════════════

def _parse_profile(html: str) -> HemisProfile:
    s = BeautifulSoup(html, "html.parser")

    # Standart Hemis profil sahifasi: info jadvaldan ma'lumot olish
    info = {}
    for row in s.select("table tr, .profile-info tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower()
            val = cells[1].get_text(strip=True)
            info[key] = val

    def find_val(*keys) -> str:
        for k in keys:
            for ik, iv in info.items():
                if any(kk in ik for kk in k.split("|")):
                    return iv
        return ""

    full_name  = find_val("f.i.sh|ф.и.о|ism|fish|талаба")
    group      = find_val("guruh|группа|group")
    faculty    = find_val("fakultet|факультет|faculty")
    semester   = find_val("semestr|семестр")
    student_id = find_val("hemis|id|raqam|студент")
    level      = find_val("daraja|степень|level|ta'lim turi")
    study_form = find_val("ta'lim shakli|форма|form")

    # Agar jadvaldan topa olmadik — boshqa selectorlar
    if not full_name:
        el = s.select_one("h4, h3, .student-name, .profile-name, "
                          "[class*='name'], .user-name")
        if el: full_name = el.get_text(strip=True)

    if not group:
        el = s.select_one("[class*='group'], [data-label*='uruh']")
        if el: group = el.get_text(strip=True)

    # GPA
    gpa = None
    for el in s.select("td, .gpa, [class*='gpa']"):
        t = el.get_text(strip=True)
        if re.match(r"^\d\.\d{1,2}$", t):
            v = float(t)
            if 0 < v <= 5:
                gpa = v
                break

    return HemisProfile(
        full_name=full_name or "Noma'lum",
        student_id=student_id,
        group=group,
        faculty=faculty,
        semester=semester,
        gpa=gpa,
        level=level,
        study_form=study_form,
    )


def _parse_semesters(html: str) -> list:
    s = BeautifulSoup(html, "html.parser")
    semesters = []

    # Hemis standart: select element semester tanlash uchun
    for sel_el in s.find_all("select"):
        name = sel_el.get("name", "")
        if "semester" in name.lower() or "semestr" in name.lower():
            for opt in sel_el.find_all("option"):
                val = opt.get("value", "")
                lbl = opt.get_text(strip=True)
                selected = opt.get("selected") is not None
                if val and val != "0":
                    semesters.append({
                        "id": val,
                        "label": lbl,
                        "active": selected
                    })
            break

    # Fallback: tab yoki link
    if not semesters:
        for a in s.select("a[href*='semester'], button[data-semester]"):
            val = (a.get("href", "") or a.get("data-semester", ""))
            val = re.search(r"\d+", val)
            if val:
                semesters.append({
                    "id": val.group(),
                    "label": a.get_text(strip=True),
                    "active": "active" in " ".join(a.get("class", []))
                })

    return semesters


def _parse_grades(html: str) -> list:
    s = BeautifulSoup(html, "html.parser")
    result = []

    # TSUE Hemis: Baholar jadvali odatda table.table yoki table.table-bordered
    # Ustunlar: №, Fan nomi, Joriy(20), Oraliq(30), Yakuniy(50), Jami, Soat, NB
    table = (
        s.find("table", class_="table") or
        s.find("table", class_=re.compile(r"table")) or
        s.find("table")
    )

    if not table:
        return _demo_grades()   # jadval topilmadi — demo qaytaramiz

    for row in table.select("tbody tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        texts = [c.get_text(strip=True) for c in cols]

        # Fan nomi — 2-ustun (1-ustun tartib raqami)
        subject = texts[1] if len(texts) > 1 else texts[0]
        if not subject or len(subject) < 3 or subject.isdigit():
            continue

        # Ball ustunlari — turli Hemis versiyalarida boshqacha
        # Format: [#, Fan, Joriy/20, Oraliq/30, Yakuniy/50, Jami, Soat, NB]
        current = _f(texts[2]) if len(texts) > 2 else None
        midterm = _f(texts[3]) if len(texts) > 3 else None
        final   = _f(texts[4]) if len(texts) > 4 else None
        total   = _f(texts[5]) if len(texts) > 5 else None
        hours   = _i(texts[6]) if len(texts) > 6 else None
        missed  = _i(texts[7]) if len(texts) > 7 else None

        # Ball chegaralarini tekshiramiz
        if current is not None and current > 20: current = None
        if midterm is not None and midterm > 30: midterm = None
        if final   is not None and final   > 50: final   = None

        # Jami ball
        if total is None:
            total = (current or 0) + (midterm or 0) + (final or 0)
        if total > 100: total = None

        result.append(HemisGrade(
            subject     = _cl(subject),
            hemis_id    = texts[0],
            current     = current,
            midterm     = midterm,
            final       = final,
            total       = total,
            total_hours = hours,
            missed      = missed,
            semester    = _sem(),
        ))

    return result if result else _demo_grades()


def _parse_schedule(html: str, week_start: date) -> list:
    s = BeautifulSoup(html, "html.parser")
    lessons = []

    # TSUE Hemis jadval — ko'pincha haftalik jadval ko'rinishida
    # Har bir kun alohida section yoki tab

    # Usul 1: Kunlar bo'yicha container
    day_selectors = [
        ".schedule-day", ".timetable-day",
        "[class*='day-schedule']", "[data-week-day]",
        ".week-day-item",
    ]
    for sel in day_selectors:
        days = s.select(sel)
        if days:
            for di, day_el in enumerate(days[:7]):
                d = week_start + timedelta(days=di)
                _extract_from_day(day_el, d, lessons)
            if lessons:
                break

    # Usul 2: Haftalik jadval table
    if not lessons:
        table = s.find("table", class_=re.compile(r"schedule|timetable|jadval", re.I))
        if not table:
            table = s.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Sarlavha qatorini o'tkazib yuboramiz
                cols = row.find_all(["td", "th"])
                if not cols: continue
                # 1-ustun: dars raqami yoki vaqti
                num_text = cols[0].get_text(strip=True)
                num = _i(num_text) or 1
                # 2-7 ustun: Dushanba-Shanba
                for ci, cell in enumerate(cols[1:7]):
                    text = cell.get_text(" ", strip=True)
                    if not text or len(text) < 3: continue
                    d = week_start + timedelta(days=ci)
                    st, en = LESSON_TIMES.get(num, ("00:00","00:00"))
                    lessons.append(HemisLesson(
                        date=d.isoformat(), weekday=d.weekday(), num=num,
                        start=st, end=en,
                        subject=_cl(text[:80]), s_type="", teacher="",
                        room="", building="",
                    ))

    # Usul 3: Individual lesson cards
    if not lessons:
        cards = s.select(
            ".lesson-item, .schedule-item, [class*='lesson'],  "
            "[class*='schedule'] li, .timetable-item"
        )
        for card in cards:
            # Kun raqamini topamiz
            day_attr = (
                card.get("data-day") or
                card.get("data-week-day") or
                card.get("data-date", "")
            )
            if day_attr:
                if len(day_attr) == 10:  # ISO date
                    try:
                        d = date.fromisoformat(day_attr)
                    except: continue
                elif day_attr.isdigit():
                    di = int(day_attr)
                    d  = week_start + timedelta(days=di-1 if di > 0 else 0)
                else:
                    continue
            else:
                continue

            num_str = card.get("data-lesson", card.get("data-num", "1"))
            num     = _i(num_str) or 1
            st, en  = LESSON_TIMES.get(num, ("00:00","00:00"))

            subj = _txt_first(card,
                ".subject", ".lesson-name", ".discipline",
                "[class*='subject']", "strong", "b", "h5", "h6"
            )
            if not subj or len(subj) < 3: continue

            lessons.append(HemisLesson(
                date    = d.isoformat(),
                weekday = d.weekday(),
                num     = num,
                start   = st,
                end     = en,
                subject = _cl(subj),
                s_type  = _cl(_txt_first(card, ".type", "[class*='type']")),
                teacher = _cl(_txt_first(card, ".teacher", "[class*='teacher']", "[class*='professor']")),
                room    = _cl(_txt_first(card, ".room", ".auditoriya", "[class*='room']")),
                building= _cl(_txt_first(card, ".building", ".bino", "[class*='build']")),
            ))

    return sorted(lessons, key=lambda l: (l.date, l.num))


def _extract_from_day(day_el, d: date, lessons: list):
    """Bir kunlik container dan darslarni olish"""
    cells = day_el.select(
        ".lesson-cell, .lesson, tr, .time-row, [class*='lesson']"
    )
    for cell in cells:
        num_text = _txt_first(cell, ".num", ".lesson-number", "[class*='num']")
        num = _i(num_text) or 1
        st, en = LESSON_TIMES.get(num, ("00:00","00:00"))

        subj = _txt_first(cell,
            ".subject", ".discipline", ".lesson-name",
            "[class*='subject']", "strong", "b"
        )
        if not subj or len(subj) < 3: continue

        lessons.append(HemisLesson(
            date    = d.isoformat(),
            weekday = d.weekday(),
            num     = num,
            start   = st,
            end     = en,
            subject = _cl(subj),
            s_type  = _cl(_txt_first(cell, ".type", "[class*='type']")),
            teacher = _cl(_txt_first(cell, ".teacher", "[class*='teacher']")),
            room    = _cl(_txt_first(cell, ".room", ".auditoriya")),
            building= _cl(_txt_first(cell, ".building", "[class*='build']")),
        ))


# ── Utils ─────────────────────────────────────────────────────

def _txt_first(el, *selectors) -> str:
    for sel in selectors:
        found = el.select_one(sel)
        if found:
            return found.get_text(strip=True)
    return ""

def _cl(t: str) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip()

def _f(t) -> Optional[float]:
    if t is None: return None
    s = str(t).replace(",", ".").strip()
    m = re.search(r"\d+\.?\d*", s)
    return float(m.group()) if m else None

def _i(t) -> Optional[int]:
    if t is None: return None
    m = re.search(r"\d+", str(t))
    return int(m.group()) if m else None

def _sem() -> str:
    from datetime import datetime
    n = datetime.now()
    return f"{n.year}-{1 if n.month <= 6 else 2}"


# ── Demo Data ─────────────────────────────────────────────────

def _demo_profile() -> HemisProfile:
    return HemisProfile(
        full_name="Demo Talaba", student_id="U2200000",
        group="IQ-22-01", faculty="Iqtisodiyot",
        semester="2024-2025 (2-semestr)", gpa=3.45,
        level="Bakalavr", study_form="Kunduzgi",
    )

def _demo_grades() -> list:
    data = [
        ("Mikroiqtisodiyot",      "1", 17, 24, None, 41, 64,  4),
        ("Bank ishi va kredit",   "2", 15, 22, None, 37, 72,  6),
        ("Iqtisodiy siyosat",     "3", 18, 28, None, 46, 80,  2),
        ("Pul va kredit",         "4", 12, 18, None, 30, 64, 14),
        ("Marketing asoslari",    "5", 19, 26, None, 45, 72,  0),
        ("Tadbirkorlik asoslari", "6", 16, 25, None, 41, 56,  6),
    ]
    return [
        HemisGrade(s, h, c, m, f, t, hr, ms, "2024-2")
        for s, h, c, m, f, t, hr, ms in data
    ]

def _demo_schedule(target: date) -> list:
    monday = target - timedelta(days=target.weekday())
    items = [
        (0, 1, "Mikroiqtisodiyot",     "Ma'ruza", "Salimov B.",   "A-301", "A blok"),
        (0, 3, "Bank ishi",            "Seminar",  "Rahimov N.",   "B-204", "B blok"),
        (1, 2, "Pul va kredit",        "Ma'ruza", "Hasanov M.",   "A-101", "A blok"),
        (1, 4, "Marketing",            "Seminar",  "Yusupov K.",   "C-305", "C blok"),
        (2, 1, "Iqtisodiy siyosat",    "Ma'ruza", "Toshmatov A.", "A-201", "A blok"),
        (3, 2, "Mikroiqtisodiyot",     "Seminar",  "Salimov B.",   "B-102", "B blok"),
        (4, 3, "Bank ishi",            "Ma'ruza", "Rahimov N.",   "A-301", "A blok"),
    ]
    result = []
    for di, num, subj, stype, teacher, room, building in items:
        d = monday + timedelta(days=di)
        st, en = LESSON_TIMES[num]
        result.append(HemisLesson(
            d.isoformat(), d.weekday(), num,
            st, en, subj, stype, teacher, room, building
        ))
    return sorted(result, key=lambda l: (l.date, l.num))
