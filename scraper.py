"""
scraper.py — TSUE Hemis REST API v1 scraper
API endpoint: https://talaba.tsue.uz/rest/v1/
"""
import aiohttp
import asyncio
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
import hashlib
import config

# ── Hemis REST API headers ────────────────────────────────────
HEADERS = {
    "User-Agent": "HEMISStudent/1.0 (Android)",
    "Accept": "application/json",
    "Content-Type": "application/json",
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
    """
    TSUE Hemis REST API orqali ma'lumot olish.
    Endpoint: https://talaba.tsue.uz/rest/v1/
    """

    def __init__(self, user_id, hemis_id, enc_password,
                 demo=False, cookies=None):
        self.user_id   = user_id
        self.hemis_id  = hemis_id
        self._enc_pass = enc_password
        self.demo      = demo
        self._token    = None          # Bearer token
        self._session  = None
        self._base     = config.HEMIS_BASE_URL.rstrip("/")
        self._api      = self._base + "/rest/v1"

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)
        timeout   = aiohttp.ClientTimeout(total=30, connect=10)
        self._session = aiohttp.ClientSession(
            headers=HEADERS,
            timeout=timeout,
            connector=connector,
        )
        return self

    async def __aexit__(self, *_):
        if self._session:
            await self._session.close()

    # ── Public API ────────────────────────────────────────────

    async def ensure_login(self):
        if self.demo:
            return
        if self._token:
            return
        await self._login()

    async def get_cookies_dict(self) -> dict:
        """Token ni saqlash uchun"""
        return {"token": self._token or ""}

    async def fetch_profile(self) -> HemisProfile:
        if self.demo:
            return _demo_profile()
        data = await self._get("/account/me")
        return _parse_profile_api(data)

    async def fetch_grades(self, semester_id: str = "") -> list:
        if self.demo:
            return _demo_grades()
        params = {}
        if semester_id:
            params["semester_id"] = semester_id
        data = await self._get("/student/performance", params=params)
        return _parse_grades_api(data)

    async def fetch_semesters(self) -> list:
        if self.demo:
            return [
                {"id":"162","label":"2024-2025 (2-semestr)","active":True},
                {"id":"161","label":"2024-2025 (1-semestr)","active":False},
                {"id":"160","label":"2023-2024 (2-semestr)","active":False},
                {"id":"159","label":"2023-2024 (1-semestr)","active":False},
            ]
        data = await self._get("/data/semesters")
        return _parse_semesters_api(data)

    async def fetch_schedule(self, target: Optional[date] = None) -> list:
        if self.demo:
            return _demo_schedule(target or date.today())
        td     = target or date.today()
        monday = td - timedelta(days=td.weekday())
        data   = await self._get("/student/time-table", params={
            "week": monday.isoformat(),
            "month": monday.strftime("%Y-%m"),
        })
        return _parse_schedule_api(data, monday)

    async def fetch_raw_html(self, path: str) -> str:
        """Debug uchun — REST API javobini tekshirish"""
        if self.demo:
            return '{"demo": true}'
        return await self._get_raw(path)

    async def inspect_api(self) -> dict:
        """API endpointlarini tekshirish uchun"""
        results = {}
        endpoints = [
            "/account/me",
            "/student/performance",
            "/student/time-table",
            "/data/semesters",
            "/data/academic-years",
        ]
        for ep in endpoints:
            try:
                data = await self._get(ep)
                results[ep] = {
                    "status": "ok",
                    "keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
                    "sample": str(data)[:200],
                }
            except Exception as e:
                results[ep] = {"status": "error", "error": str(e)}
        return results

    # ── Internal ──────────────────────────────────────────────

    async def _login(self):
        from crypto import decrypt
        password = decrypt(self._enc_pass)

        # REST API login
        async with self._session.post(
            self._api + "/auth/login",
            json={
                "login": self.hemis_id,
                "password": password,
            }
        ) as r:
            if r.status == 401:
                raise HemisAuthError(
                    "Login ID yoki parol noto'g'ri!\n"
                    "talaba.tsue.uz dagi login va parolingizni kiriting."
                )
            if r.status != 200:
                # Fallback: eski web login
                await self._login_web(password)
                return

            data = await r.json()

        # Token olish
        token = (
            data.get("data", {}).get("token") or
            data.get("token") or
            data.get("access_token") or
            data.get("data", {}).get("access_token")
        )

        if not token:
            # Muvaffaqiyatli login bo'ldi lekin token yo'q
            # Web login ga o'tamiz
            await self._login_web(password)
            return

        self._token = token
        self._session.headers.update({
            "Authorization": f"Bearer {token}"
        })

    async def _login_web(self, password: str):
        """Fallback: Web sesion orqali login"""
        from bs4 import BeautifulSoup

        login_url = self._base + "/dashboard/login"

        async with self._session.get(login_url) as r:
            html = await r.text()

        soup = BeautifulSoup(html, "html.parser")

        # CSRF
        csrf_name  = "_csrf-frontend"
        csrf_token = ""
        for inp in soup.find_all("input"):
            name = inp.get("name","")
            if "csrf" in name.lower():
                csrf_name  = name
                csrf_token = inp.get("value","")
                break

        # Username/password field nomlari
        username_field = "LoginForm[username]"
        password_field = "LoginForm[password]"
        for inp in soup.find_all("input"):
            itype = inp.get("type","")
            iname = inp.get("name","")
            if itype == "password" and iname:
                password_field = iname
            if itype == "text" and iname and "csrf" not in iname.lower():
                username_field = iname

        form_data = {
            csrf_name:      csrf_token,
            username_field: self.hemis_id,
            password_field: password,
            "LoginForm[rememberMe]": "1",
        }

        async with self._session.post(
            login_url,
            data=form_data,
            allow_redirects=True,
        ) as r:
            final_url = str(r.url)

        if "/dashboard/login" in final_url:
            raise HemisAuthError(
                "Login muvaffaqiyatsiz!\n"
                "talaba.tsue.uz dagi login va parolingizni kiriting.\n\n"
                "Login — bu passportingiz seriyasi yoki talaba ID raqami."
            )

        # Web session uchun token yo'q, cookie ishlatiladi
        self._token = "web_session"

    async def _get(self, path: str, params: dict = None) -> dict:
        """JSON API so'rovi"""
        url = self._api + path
        try:
            async with self._session.get(
                url,
                params=params,
                allow_redirects=True,
            ) as r:
                if r.status == 401:
                    # Token muddati o'tgan
                    self._token = None
                    await self._login()
                    return await self._get(path, params)

                content_type = r.content_type or ""
                if "json" in content_type:
                    data = await r.json()
                else:
                    text = await r.text()
                    import json as _json
                    try:
                        data = _json.loads(text)
                    except Exception:
                        raise HemisError(f"JSON emas: {text[:200]}")

                # Hemis API javob formati: {data: {...}, status: true}
                if isinstance(data, dict):
                    if "data" in data:
                        return data["data"]
                    return data
                return {"items": data}

        except aiohttp.ClientError as e:
            raise HemisError(f"Ulanib bo'lmadi: {e}")

    async def _get_raw(self, path: str) -> str:
        url = self._api + path
        try:
            async with self._session.get(url, allow_redirects=True) as r:
                return await r.text()
        except Exception as e:
            return str(e)


# ══════════════════════════════════════════════════════════
# API Parsers — JSON ma'lumotlarni parse qilish
# ══════════════════════════════════════════════════════════

def _parse_profile_api(data: dict) -> HemisProfile:
    """
    Hemis /account/me API javobini parse qilish.
    Javob formati har xil bo'lishi mumkin.
    """
    if not data:
        return _demo_profile()

    # Ism
    full_name = (
        data.get("full_name") or
        data.get("name") or
        (
            (data.get("firstname") or "") + " " +
            (data.get("surname")   or "") + " " +
            (data.get("patronymic") or "")
        ).strip() or
        "Noma'lum"
    )

    # Guruh
    group = ""
    group_data = data.get("group") or data.get("student_id_number", {})
    if isinstance(group_data, dict):
        group = group_data.get("name","") or group_data.get("code","")
    elif isinstance(group_data, str):
        group = group_data

    # Fakultet
    faculty = ""
    faculty_data = data.get("faculty") or data.get("department",{})
    if isinstance(faculty_data, dict):
        faculty = faculty_data.get("name","")
    elif isinstance(faculty_data, str):
        faculty = faculty_data

    # Semestr
    semester = ""
    sem_data = data.get("semester") or data.get("current_semester", {})
    if isinstance(sem_data, dict):
        semester = sem_data.get("name","") or sem_data.get("code","")
    elif isinstance(sem_data, str):
        semester = sem_data

    gpa = None
    gpa_raw = data.get("gpa") or data.get("avg_grade")
    if gpa_raw is not None:
        try:
            gpa = float(gpa_raw)
        except Exception:
            pass

    return HemisProfile(
        full_name  = full_name,
        student_id = str(data.get("login","") or data.get("id","")),
        group      = group,
        faculty    = faculty,
        semester   = semester,
        gpa        = gpa,
        level      = str(data.get("level","") or data.get("education_type","")),
        study_form = str(data.get("study_form","") or data.get("education_form","")),
    )


def _parse_grades_api(data) -> list:
    """
    Hemis /student/performance API javobini parse qilish.
    """
    if not data:
        return _demo_grades()

    # Ro'yxat formatlar
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = (
            data.get("items") or
            data.get("grades") or
            data.get("performances") or
            data.get("list") or
            []
        )

    if not items:
        return _demo_grades()

    result = []
    for item in items:
        if not isinstance(item, dict):
            continue

        # Fan nomi
        subject_data = item.get("subject") or item.get("discipline") or {}
        if isinstance(subject_data, dict):
            subject = subject_data.get("name","") or subject_data.get("code","")
        else:
            subject = str(subject_data)

        if not subject:
            subject = item.get("subject_name","") or item.get("name","")

        if not subject or len(subject) < 2:
            continue

        # Ballar
        def _fv(key):
            v = item.get(key)
            if v is None: return None
            try: return float(v)
            except: return None

        current = _fv("current") or _fv("rating_current") or _fv("score1") or _fv("ball1")
        midterm = _fv("midterm") or _fv("rating_midterm") or _fv("score2") or _fv("ball2")
        final   = _fv("final")   or _fv("rating_final")   or _fv("score3") or _fv("ball3")
        total   = _fv("total")   or _fv("rating_total")   or _fv("total_score") or _fv("ball")

        # Soatlar
        hours  = item.get("total_hours") or item.get("hours") or item.get("credit_hours")
        missed = item.get("missed_hours") or item.get("missed") or item.get("absent")

        if total is None:
            total = (current or 0) + (midterm or 0) + (final or 0)

        result.append(HemisGrade(
            subject     = subject.strip(),
            hemis_id    = str(item.get("id","") or item.get("subject_id","")),
            current     = current,
            midterm     = midterm,
            final       = final,
            total       = total,
            total_hours = int(hours) if hours else None,
            missed      = int(missed) if missed else 0,
            semester    = _sem(),
        ))

    return result if result else _demo_grades()


def _parse_semesters_api(data) -> list:
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("items") or data.get("semesters") or []

    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result.append({
            "id":     str(item.get("id","") or item.get("code","")),
            "label":  item.get("name","") or item.get("code",""),
            "active": bool(item.get("current") or item.get("is_current") or item.get("active")),
        })
    return result


def _parse_schedule_api(data, week_start: date) -> list:
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = (
            data.get("items") or
            data.get("schedule") or
            data.get("lessons") or
            data.get("timetable") or
            []
        )

    if not items:
        return _demo_schedule(week_start)

    lessons = []
    for item in items:
        if not isinstance(item, dict):
            continue

        # Fan
        subj_data = item.get("subject") or item.get("lesson") or {}
        if isinstance(subj_data, dict):
            subject = subj_data.get("name","")
        else:
            subject = str(subj_data or "")

        if not subject:
            subject = item.get("subject_name","") or item.get("name","")
        if not subject or len(subject) < 2:
            continue

        # Kun va vaqt
        day_val = item.get("day_of_week") or item.get("weekday") or item.get("day")
        num_val = item.get("lesson_num")  or item.get("pair")    or item.get("num") or 1
        date_str= item.get("date","")     or item.get("lesson_date","")

        try:
            num = int(num_val)
        except Exception:
            num = 1

        if date_str and len(date_str) >= 10:
            try:
                d = date.fromisoformat(date_str[:10])
            except Exception:
                d = week_start
        elif day_val is not None:
            try:
                di = int(day_val) - 1  # 1=Du → 0
                d  = week_start + timedelta(days=max(0, min(di, 6)))
            except Exception:
                d = week_start
        else:
            d = week_start

        st = item.get("start_time","") or item.get("time_start","")
        en = item.get("end_time","")   or item.get("time_end","")
        if not st:
            st, en = LESSON_TIMES.get(num, ("00:00","00:00"))

        # O'qituvchi
        teacher_data = item.get("teacher") or item.get("lecturer") or {}
        if isinstance(teacher_data, dict):
            teacher = (
                teacher_data.get("full_name","") or
                teacher_data.get("name","") or
                (teacher_data.get("surname","") + " " + teacher_data.get("firstname","")[:1]+".").strip()
            )
        else:
            teacher = str(teacher_data or "")

        # Auditoriya
        room_data = item.get("room") or item.get("auditorium") or item.get("classroom") or {}
        if isinstance(room_data, dict):
            room     = room_data.get("code","") or room_data.get("name","")
            building = room_data.get("building","") or room_data.get("corpus","")
        else:
            room     = str(room_data or "")
            building = ""

        lessons.append(HemisLesson(
            date    = d.isoformat(),
            weekday = d.weekday(),
            num     = num,
            start   = st[:5] if st else "00:00",
            end     = en[:5] if en else "00:00",
            subject = subject.strip(),
            s_type  = str(item.get("lesson_type","") or item.get("type","")),
            teacher = teacher.strip(),
            room    = room.strip(),
            building= building.strip(),
        ))

    return sorted(lessons, key=lambda l: (l.date, l.num))


# ── Utils ─────────────────────────────────────────────────────

def _sem() -> str:
    from datetime import datetime
    n = datetime.now()
    return f"{n.year}-{1 if n.month<=6 else 2}"


# ── Demo Data ─────────────────────────────────────────────────

def _demo_profile():
    return HemisProfile(
        "Demo Talaba","U2200000","IQ-22-01",
        "Iqtisodiyot","2024-2025 (2-semestr)",
        3.45,"Bakalavr","Kunduzgi"
    )

def _demo_grades():
    data = [
        ("Mikroiqtisodiyot",      "1",17,24,None,41,64,4),
        ("Bank ishi va kredit",   "2",15,22,None,37,72,6),
        ("Iqtisodiy siyosat",     "3",18,28,None,46,80,2),
        ("Pul va kredit",         "4",12,18,None,30,64,14),
        ("Marketing asoslari",    "5",19,26,None,45,72,0),
        ("Tadbirkorlik asoslari", "6",16,25,None,41,56,6),
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
