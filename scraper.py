"""
scraper.py — Hemis scraper + Demo ma'lumotlar
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
import hashlib, re
import config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "uz,en;q=0.9",
}

TIMES = {
    1: ("08:30","09:50"), 2: ("10:00","11:20"), 3: ("11:30","12:50"),
    4: ("13:30","14:50"), 5: ("15:00","16:20"), 6: ("16:30","17:50"),
    7: ("18:00","19:20"),
}


@dataclass
class HemisGrade:
    subject: str
    hemis_id: str
    current: Optional[float]
    midterm: Optional[float]
    final: Optional[float]
    total: Optional[float]
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


class HemisAuthError(Exception): pass
class HemisError(Exception): pass


class HemisScraper:
    def __init__(self, user_id, hemis_id, enc_password, demo=False, cookies=None):
        self.user_id      = user_id
        self.hemis_id     = hemis_id
        self._enc_pass    = enc_password
        self.demo         = demo
        self._cookies     = cookies or {}
        self._session     = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(
            base_url=config.HEMIS_BASE_URL,
            headers=HEADERS,
            timeout=timeout,
        )
        if self._cookies:
            self._session.cookie_jar.update_cookies(self._cookies)
        return self

    async def __aexit__(self, *_):
        if self._session:
            await self._session.close()

    async def ensure_login(self):
        if self.demo: return
        if await self._valid_session(): return
        await self._login()

    async def _valid_session(self):
        if not self._cookies: return False
        try:
            async with self._session.get("/dashboard", allow_redirects=False) as r:
                return r.status == 200
        except: return False

    async def _login(self):
        from crypto import decrypt
        password = decrypt(self._enc_pass)
        async with self._session.get("/dashboard/login") as r:
            html = await r.text()
        soup = BeautifulSoup(html, "html.parser")
        csrf = soup.find("input", {"name": "_csrf-frontend"})
        if not csrf: raise HemisAuthError("CSRF topilmadi")
        async with self._session.post("/dashboard/login", data={
            "_csrf-frontend": csrf.get("value",""),
            "LoginForm[username]": self.hemis_id,
            "LoginForm[password]": password,
            "LoginForm[rememberMe]": "1",
        }, allow_redirects=True) as r:
            if "/dashboard/login" in str(r.url):
                raise HemisAuthError("Hemis ID yoki parol noto'g'ri!")

    async def fetch_profile(self) -> HemisProfile:
        if self.demo: return _demo_profile()
        html = await self._get("/dashboard/student-info")
        return _parse_profile(html)

    async def fetch_grades(self) -> list[HemisGrade]:
        if self.demo: return _demo_grades()
        html = await self._get("/student/performance")
        return _parse_grades(html)

    async def fetch_schedule(self, target: Optional[date]=None) -> list[HemisLesson]:
        if self.demo: return _demo_schedule(target or date.today())
        td = target or date.today()
        monday = td - timedelta(days=td.weekday())
        html = await self._get(f"/student/time-table?week={monday.isoformat()}")
        return _parse_schedule(html, monday)

    async def _get(self, path, attempt=1) -> str:
        try:
            async with self._session.get(path, allow_redirects=True) as r:
                if "/dashboard/login" in str(r.url):
                    await self._login()
                    return await self._get(path)
                r.raise_for_status()
                return await r.text()
        except aiohttp.ClientError as e:
            if attempt < 3:
                await asyncio.sleep(2 ** attempt)
                return await self._get(path, attempt+1)
            raise HemisError(str(e))


# ── Parsers ────────────────────────────────────────────────────────────────────
def _parse_profile(html):
    s = BeautifulSoup(html, "html.parser")
    def t(sel): el=s.select_one(sel); return el.get_text(strip=True) if el else ""
    return HemisProfile(
        full_name=t(".student-name,.profile-name"),
        student_id=t("[data-field='id_number']"),
        group=t("[data-field='group']"),
        faculty=t("[data-field='faculty']"),
        semester=t("[data-field='semester']"),
        gpa=_f(t(".gpa-value,[data-field='gpa']")),
    )

def _parse_grades(html):
    s = BeautifulSoup(html, "html.parser")
    result = []
    for row in s.select("table.table tbody tr"):
        c = row.find_all("td")
        if len(c) < 8: continue
        result.append(HemisGrade(
            subject=c[1].get_text(strip=True), hemis_id=c[0].get_text(strip=True),
            current=_f(c[2].get_text()), midterm=_f(c[3].get_text()),
            final=_f(c[4].get_text()), total=_f(c[5].get_text()),
            total_hours=_i(c[6].get_text()), missed=_i(c[7].get_text()),
            semester=_sem(),
        ))
    return result

def _parse_schedule(html, week_start):
    s = BeautifulSoup(html, "html.parser")
    lessons = []
    for di, day in enumerate(s.select(".timetable-day,.schedule-day")):
        d = week_start + timedelta(days=di)
        for cell in day.select(".lesson-cell,tr.lesson"):
            c = cell.find_all("td")
            if not c: continue
            num = _i(c[0].get_text()) or 1
            st, en = TIMES.get(num, ("00:00","00:00"))
            lessons.append(HemisLesson(
                date=d.isoformat(), weekday=d.weekday(), num=num, start=st, end=en,
                subject=_cl(c[1].get_text() if len(c)>1 else ""),
                s_type=_cl(c[2].get_text() if len(c)>2 else ""),
                teacher=_cl(c[3].get_text() if len(c)>3 else ""),
                room=_cl(c[4].get_text() if len(c)>4 else ""),
                building=_cl(c[5].get_text() if len(c)>5 else ""),
            ))
    return sorted(lessons, key=lambda l: (l.date, l.num))

def _cl(t): return re.sub(r"\s+"," ",t).strip()
def _f(t):
    m = re.search(r"[\d.]+", t.replace(",","."))
    return float(m.group()) if m else None
def _i(t):
    m = re.search(r"\d+", t)
    return int(m.group()) if m else None
def _sem():
    from datetime import datetime
    n=datetime.now(); return f"{n.year}-{1 if n.month<=6 else 2}"


# ── Demo data ──────────────────────────────────────────────────────────────────
def _demo_profile():
    return HemisProfile("Demo Talaba","U2200000","IM-22-01","Iqtisodiyot","2024-2",3.45)

def _demo_grades():
    return [
        HemisGrade("Mikroiqtisodiyot","MIK01",17,24,None,41,64,4,"2024-2"),
        HemisGrade("Bank ishi","BNK02",15,22,None,37,72,6,"2024-2"),
        HemisGrade("Iqtisodiy siyosat","IQS03",18,28,None,46,80,2,"2024-2"),
        HemisGrade("Pul va kredit","PUL04",12,18,None,30,64,8,"2024-2"),
        HemisGrade("Marketing","MRK05",19,26,None,45,72,0,"2024-2"),
    ]

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
        st,en = TIMES[num]
        result.append(HemisLesson(d.isoformat(),d.weekday(),num,st,en,subj,stype,teacher,room,building))
    return sorted(result, key=lambda l:(l.date,l.num))
