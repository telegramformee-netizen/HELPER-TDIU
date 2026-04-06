"""
scraper.py — TDIU Hemis scraper
Real TDIU Hemis saytiga moslashtirilgan.
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
import hashlib, re, json
import config

# ── Hemis URL ─────────────────────────────────────────────────
# TDIU uchun to'g'ri URL — config.py da HEMIS_BASE_URL o'rnating
# Odatda: https://student.hemis.uz yoki https://hemis.tdiu.uz

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "uz-UZ,uz;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

LESSON_TIMES = {
    1: ("08:30","09:50"),
    2: ("10:00","11:20"),
    3: ("11:30","12:50"),
    4: ("13:30","14:50"),
    5: ("15:00","16:20"),
    6: ("16:30","17:50"),
    7: ("18:00","19:20"),
    8: ("20:00","21:20"),
}


# ── Data classes ──────────────────────────────────────────────

@dataclass
class HemisGrade:
    subject: str
    hemis_id: str
    current: Optional[float]   # max 20
    midterm: Optional[float]   # max 30
    final:   Optional[float]   # max 50
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
    level: str = ""       # "Bakalavr", "Magistr"
    study_form: str = ""  # "Kunduzgi", "Sirtqi"


class HemisAuthError(Exception): pass
class HemisError(Exception): pass


# ── Main Scraper ──────────────────────────────────────────────

class HemisScraper:
    """
    Hemis scraper — cookie-based session qayta ishlatiladi.
    Demo mode da haqiqiy so'rovlar yuborilmaydi.
    """

    def __init__(
        self,
        user_id: int,
        hemis_id: Optional[str],
        enc_password: Optional[str],
        demo: bool = False,
        cookies: Optional[dict] = None,
    ):
        self.user_id     = user_id
        self.hemis_id    = hemis_id
        self._enc_pass   = enc_password
        self.demo        = demo
        self._cookies    = cookies or {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._base       = config.HEMIS_BASE_URL.rstrip("/")

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)  # Ba'zi Hemis serverlar SSL sertifikat muammosi
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

    # ── Public API ────────────────────────────────────────────

    async def ensure_login(self):
        if self.demo:
            return
        if await self._is_session_valid():
            return
        await self._do_login()

    async def get_cookies_dict(self) -> dict:
        """DB ga saqlash uchun cookie dict qaytaradi"""
        return {c.key: c.value for c in self._session.cookie_jar}

    async def fetch_profile(self) -> HemisProfile:
        if self.demo:
            return _demo_profile()
        html = await self._get("/dashboard/student-info")
        return _parse_profile(html)

    async def fetch_grades(self, semester_id: str = "") -> list[HemisGrade]:
        if self.demo:
            return _demo_grades()
        path = "/student/performance"
        if semester_id:
            path += f"?semester_id={semester_id}"
        html = await self._get(path)
        return _parse_grades(html)

    async def fetch_semesters(self) -> list[dict]:
        """Mavjud semestrlar ro'yxati"""
        if self.demo:
            return [
                {"id": "2024-2", "label": "2024-2 (Bahor)", "active": True},
                {"id": "2024-1", "label": "2024-1 (Kuz)",   "active": False},
            ]
        html = await self._get("/student/performance")
        return _parse_semesters(html)

    async def fetch_schedule(self, target: Optional[date] = None) -> list[HemisLesson]:
        if self.demo:
            return _demo_schedule(target or date.today())
        td     = target or date.today()
        monday = td - timedelta(days=td.weekday())
        # Hemis week parametri uchun turli formatlar sinab ko'riladi
        html = await self._get(f"/student/time-table?week={monday.isoformat()}")
        lessons = _parse_schedule(html, monday)
        if not lessons:
            # Fallback: boshqa format
            html = await self._get(
                f"/student/time-table?date={monday.strftime('%d.%m.%Y')}"
            )
            lessons = _parse_schedule(html, monday)
        return lessons

    async def fetch_raw_html(self, path: str) -> str:
        """Debug uchun — raw HTML qaytaradi"""
        if self.demo:
            return "<html><body>Demo mode — real HTML yo'q</body></html>"
        return await self._get(path)

    # ── Internal ──────────────────────────────────────────────

    async def _is_session_valid(self) -> bool:
        if not self._cookies:
            return False
        try:
            url = self._base + "/dashboard"
            async with self._session.get(url, allow_redirects=False) as r:
                # Login sahifasiga redirect bo'lmasa — session hali ishlaydi
                return r.status == 200 and "login" not in str(r.url).lower()
        except Exception:
            return False

    async def _do_login(self):
        from crypto import decrypt
        password = decrypt(self._enc_pass)

        # Step 1: Login sahifasini olamiz
        login_url = self._base + "/dashboard/login"
        async with self._session.get(login_url) as r:
            html = await r.text()

        soup = BeautifulSoup(html, "html.parser")

        # CSRF tokenini qidiramiz — har xil nom bo'lishi mumkin
        csrf_token = ""
        for name in ["_csrf-frontend", "_csrf", "csrf_token", "_token"]:
            inp = soup.find("input", {"name": name})
            if inp:
                csrf_token = inp.get("value", "")
                csrf_name  = name
                break

        # Step 2: Login form yuboramiz
        form_data = {
            csrf_name if csrf_token else "_csrf-frontend": csrf_token,
            "LoginForm[username]": self.hemis_id,
            "LoginForm[password]": password,
            "LoginForm[rememberMe]": "1",
        }

        async with self._session.post(
            login_url,
            data=form_data,
            allow_redirects=True,
        ) as r:
            final_url = str(r.url).lower()
            # Login sahifasida qoldik — credentials noto'g'ri
            if "login" in final_url:
                raise HemisAuthError(
                    "Hemis ID yoki parol noto'g'ri! "
                    "TDIU Hemis tizimidagi login va parolingizni tekshiring."
                )
            content = await r.text()
            # Xato xabarlarini tekshiramiz
            if any(err in content.lower() for err in [
                "incorrect", "xato", "noto'g'ri", "invalid", "error"
            ]):
                raise HemisAuthError("Login muvaffaqiyatsiz. Parolni tekshiring.")

    async def _get(self, path: str, attempt: int = 1) -> str:
        url = self._base + path
        try:
            async with self._session.get(url, allow_redirects=True) as r:
                # Session muddati o'tgan — qayta login
                if "login" in str(r.url).lower() and attempt == 1:
                    await self._do_login()
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


# ── HTML Parsers ───────────────────────────────────────────────────────────────

def _parse_profile(html: str) -> HemisProfile:
    s = BeautifulSoup(html, "html.parser")

    def txt(*selectors) -> str:
        for sel in selectors:
            el = s.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return ""

    # Ko'p xil selector sinab ko'ramiz
    full_name = txt(
        "h4.student-name", ".profile-info h4", ".student-name",
        "h3.user-name", ".info-block .name",
        "td[data-label='F.I.Sh']", "td[data-label='ФИО']",
    )
    group = txt(
        "[data-label='Guruh']", "[data-label='Группа']",
        "td:contains('Guruh') + td", ".group-name",
    )
    faculty = txt(
        "[data-label='Fakultet']", "[data-label='Факультет']",
        "td:contains('Fakultet') + td",
    )
    semester = txt(
        "[data-label='Semestr']", ".semester-name",
        "td:contains('Semestr') + td",
    )
    gpa_str = txt(".gpa-value", "[data-label='GPA']", ".gpa")
    student_id = txt(
        "[data-label='Talaba ID']", "[data-label='Hemis ID']",
        ".student-id",
    )

    # GPA ni oldik emas — jadvaldan topishga urinamiz
    if not gpa_str:
        for td in s.find_all("td"):
            text = td.get_text(strip=True)
            if re.match(r"^\d\.\d+$", text) and float(text) <= 5:
                gpa_str = text
                break

    return HemisProfile(
        full_name  = full_name or "Noma'lum",
        student_id = student_id,
        group      = group,
        faculty    = faculty,
        semester   = semester,
        gpa        = _f(gpa_str),
    )


def _parse_grades(html: str) -> list[HemisGrade]:
    s = BeautifulSoup(html, "html.parser")
    result = []

    # Usul 1: Standart table.table
    rows = s.select("table.table tbody tr, table tbody tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        texts = [c.get_text(strip=True) for c in cols]

        # Fan nomi — odatda 2-ustun
        subject = texts[1] if len(texts) > 1 else texts[0]
        if not subject or len(subject) < 3:
            continue

        # Ballarni turli ustun tartiblarida sinab ko'ramiz
        # Format 1: №, Fan, Joriy(20), Oraliq(30), Yakuniy(50), Jami, ...
        current = _f(texts[2]) if len(texts) > 2 else None
        midterm = _f(texts[3]) if len(texts) > 3 else None
        final   = _f(texts[4]) if len(texts) > 4 else None
        total   = _f(texts[5]) if len(texts) > 5 else None
        hours   = _i(texts[6]) if len(texts) > 6 else None
        missed  = _i(texts[7]) if len(texts) > 7 else None

        # Jami ball hisoblaymiz agar yo'q bo'lsa
        if total is None and any(v is not None for v in [current, midterm, final]):
            total = (current or 0) + (midterm or 0) + (final or 0)

        result.append(HemisGrade(
            subject    = _cl(subject),
            hemis_id   = texts[0] if len(texts) > 0 else "",
            current    = _clamp(current, 0, 20),
            midterm    = _clamp(midterm, 0, 30),
            final      = _clamp(final,   0, 50),
            total      = _clamp(total,   0, 100),
            total_hours= hours,
            missed     = missed,
            semester   = _sem(),
        ))

    # Usul 2: Data-attribute based
    if not result:
        for item in s.select("[data-subject], .grade-item, .performance-row"):
            subject = (
                item.get("data-subject") or
                _txt(item, ".subject-name, .fan-name")
            )
            if not subject:
                continue
            result.append(HemisGrade(
                subject    = _cl(subject),
                hemis_id   = item.get("data-id", ""),
                current    = _f(item.get("data-current", "") or _txt(item, ".current")),
                midterm    = _f(item.get("data-midterm", "") or _txt(item, ".midterm")),
                final      = _f(item.get("data-final",   "") or _txt(item, ".final")),
                total      = _f(item.get("data-total",   "") or _txt(item, ".total")),
                total_hours= _i(_txt(item, ".hours")),
                missed     = _i(_txt(item, ".missed")),
                semester   = _sem(),
            ))

    return result


def _parse_semesters(html: str) -> list[dict]:
    s = BeautifulSoup(html, "html.parser")
    semesters = []

    # Select yoki tabs orqali topamiz
    sel = s.find("select", {"name": re.compile(r"semester", re.I)})
    if sel:
        for opt in sel.find_all("option"):
            val = opt.get("value", "")
            lbl = opt.get_text(strip=True)
            selected = opt.get("selected") is not None
            if val:
                semesters.append({"id": val, "label": lbl, "active": selected})

    if not semesters:
        for tab in s.select(".semester-tab, [data-semester]"):
            val = tab.get("data-semester", tab.get("href", ""))
            lbl = tab.get_text(strip=True)
            active = "active" in (tab.get("class") or [])
            if val:
                semesters.append({"id": val, "label": lbl, "active": active})

    return semesters


def _parse_schedule(html: str, week_start: date) -> list[HemisLesson]:
    s = BeautifulSoup(html, "html.parser")
    lessons = []

    # Usul 1: Kunlar bo'yicha div
    day_containers = s.select(
        ".timetable-day, .schedule-day, "
        "[class*='day-'], [data-day], "
        ".fc-day, .week-day"
    )

    if day_containers:
        for di, day_el in enumerate(day_containers[:7]):
            d = week_start + timedelta(days=di)
            cells = day_el.select(
                ".lesson-cell, .lesson-item, tr.lesson, "
                ".schedule-item, [class*='lesson']"
            )
            for cell in cells:
                lesson = _extract_lesson(cell, d)
                if lesson:
                    lessons.append(lesson)

    # Usul 2: Haftalik table
    if not lessons:
        table = s.find("table", class_=re.compile(r"timetable|schedule|jadval", re.I))
        if table:
            for ri, row in enumerate(table.find_all("tr")[1:]):
                cols = row.find_all(["td", "th"])
                if not cols:
                    continue
                lesson_num = _i(cols[0].get_text()) or ri + 1
                for ci, cell in enumerate(cols[1:8]):
                    if not cell.get_text(strip=True):
                        continue
                    d = week_start + timedelta(days=ci)
                    lesson = _extract_lesson_from_cell(cell, d, lesson_num)
                    if lesson:
                        lessons.append(lesson)

    # Usul 3: JSON embedded
    if not lessons:
        for script in s.find_all("script"):
            text = script.string or ""
            match = re.search(r"timetable\s*=\s*(\[.*?\]);", text, re.S)
            if match:
                try:
                    data = json.loads(match.group(1))
                    lessons = _parse_schedule_json(data, week_start)
                    break
                except Exception:
                    pass

    return sorted(lessons, key=lambda l: (l.date, l.num))


def _extract_lesson(el, d: date) -> Optional[HemisLesson]:
    """HTML elementdan dars ma'lumotini olish"""
    subject = _txt(el,
        ".subject, .subject-name, .lesson-name, "
        "[class*='subject'], [data-subject], strong, b"
    )
    if not subject or len(subject) < 3:
        return None

    num_str = _txt(el, ".lesson-num, .num, [data-num]") or el.get("data-num", "1")
    num     = _i(num_str) or 1
    st, en  = LESSON_TIMES.get(num, ("00:00","00:00"))

    time_str = _txt(el, ".time, .lesson-time, [class*='time']")
    if time_str:
        times = re.findall(r"\d{1,2}:\d{2}", time_str)
        if len(times) >= 2:
            st, en = times[0], times[1]

    return HemisLesson(
        date    = d.isoformat(),
        weekday = d.weekday(),
        num     = num,
        start   = st,
        end     = en,
        subject = _cl(subject),
        s_type  = _cl(_txt(el, ".type, .lesson-type, [class*='type']")),
        teacher = _cl(_txt(el, ".teacher, .instructor, [class*='teacher']")),
        room    = _cl(_txt(el, ".room, .auditoriya, [class*='room'], [class*='audi']")),
        building= _cl(_txt(el, ".building, .bino, [class*='build']")),
    )


def _extract_lesson_from_cell(cell, d: date, num: int) -> Optional[HemisLesson]:
    text = cell.get_text(" ", strip=True)
    if not text or len(text) < 3:
        return None
    st, en = LESSON_TIMES.get(num, ("00:00","00:00"))
    return HemisLesson(
        date=d.isoformat(), weekday=d.weekday(), num=num,
        start=st, end=en, subject=_cl(text[:100]),
        s_type="", teacher="", room="", building="",
    )


def _parse_schedule_json(data: list, week_start: date) -> list[HemisLesson]:
    lessons = []
    for item in data:
        d_str = item.get("date", item.get("day", ""))
        num   = _i(str(item.get("lesson_num", item.get("num", 1)))) or 1
        st, en = LESSON_TIMES.get(num, ("00:00","00:00"))
        try:
            d = date.fromisoformat(d_str[:10]) if d_str else week_start
        except Exception:
            continue
        lessons.append(HemisLesson(
            date=d.isoformat(), weekday=d.weekday(), num=num,
            start=st, end=en,
            subject=_cl(item.get("subject", item.get("name", ""))),
            s_type =_cl(item.get("type", "")),
            teacher=_cl(item.get("teacher", "")),
            room   =_cl(item.get("room", item.get("auditoriya", ""))),
            building=_cl(item.get("building", "")),
        ))
    return lessons


# ── Utils ─────────────────────────────────────────────────────

def _cl(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()

def _txt(el, selector: str) -> str:
    found = el.select_one(selector)
    return found.get_text(strip=True) if found else ""

def _f(t) -> Optional[float]:
    if t is None: return None
    m = re.search(r"[\d]+[.,]?[\d]*", str(t).replace(",", "."))
    return float(m.group().replace(",", ".")) if m else None

def _i(t) -> Optional[int]:
    if t is None: return None
    m = re.search(r"\d+", str(t))
    return int(m.group()) if m else None

def _clamp(v, mn, mx) -> Optional[float]:
    if v is None: return None
    return max(mn, min(mx, v))

def _sem() -> str:
    from datetime import datetime
    n = datetime.now()
    return f"{n.year}-{1 if n.month <= 6 else 2}"


# ── Demo Data ─────────────────────────────────────────────────

def _demo_profile() -> HemisProfile:
    return HemisProfile(
        full_name="Demo Talaba", student_id="U2200000",
        group="IQ-22-01", faculty="Iqtisodiyot",
        semester="2024-2", gpa=3.45,
        level="Bakalavr", study_form="Kunduzgi",
    )

def _demo_grades() -> list[HemisGrade]:
    data = [
        ("Mikroiqtisodiyot",      "MIK01", 17,24,None, 41,64,4),
        ("Bank ishi va kredit",   "BNK02", 15,22,None, 37,72,6),
        ("Iqtisodiy siyosat",     "IQS03", 18,28,None, 46,80,2),
        ("Pul va kredit",         "PUL04", 12,18,None, 30,64,8),
        ("Marketing asoslari",    "MRK05", 19,26,None, 45,72,0),
        ("Tadbirkorlik asoslari", "TDB06", 16,25,None, 41,56,6),
    ]
    return [HemisGrade(s,h,c,m,f,t,hr,ms,"2024-2") for s,h,c,m,f,t,hr,ms in data]

def _demo_schedule(target: date) -> list[HemisLesson]:
    monday = target - timedelta(days=target.weekday())
    items = [
        (0,1,"Mikroiqtisodiyot","Ma'ruza", "Salimov B.", "A-301","A blok"),
        (0,3,"Bank ishi",       "Seminar", "Rahimov N.", "B-204","B blok"),
        (1,2,"Pul va kredit",   "Ma'ruza", "Hasanov M.", "A-101","A blok"),
        (1,4,"Marketing",       "Seminar", "Yusupov K.", "C-305","C blok"),
        (2,1,"Iqtisodiy siyosat","Ma'ruza","Toshmatov A.","A-201","A blok"),
        (3,2,"Mikroiqtisodiyot","Seminar", "Salimov B.", "B-102","B blok"),
        (4,3,"Bank ishi",       "Ma'ruza", "Rahimov N.", "A-301","A blok"),
    ]
    result = []
    for di, num, subj, stype, teacher, room, building in items:
        d = monday + timedelta(days=di)
        st, en = LESSON_TIMES[num]
        result.append(HemisLesson(
            d.isoformat(), d.weekday(), num, st, en,
            subj, stype, teacher, room, building
        ))
    return sorted(result, key=lambda l: (l.date, l.num))
