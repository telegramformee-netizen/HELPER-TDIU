"""
GRADES API FIX — analyzer dan NB warning va fail_risk bilan DB sync
"""

# main.py ning /api/grades/{telegram_id} qismi tuzatilsin:

@app.get("/api/grades/{telegram_id}")
async def api_grades(telegram_id: int, semester: str = ""):
    """
    DB'dan baholarni o'qiydi va analyzer orqali xavf hisoblaydi.
    NB_WARNING va FAIL_RISK DB'ga saqlaydi.
    """
    from database import Grade, User
    from analyzer import analyze
    from sqlalchemy import select, update
    
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == telegram_id))
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        q = select(Grade).where(Grade.user_id == telegram_id)
        if semester:
            q = q.where(Grade.semester == semester)
        res2 = await db.execute(q)
        grades = res2.scalars().all()

    # Analyzer qilish va xavflarni hisoblash
    analyses = []
    for g in grades:
        a = analyze(
            g.subject_name, g.current_score, g.midterm_score,
            g.final_score, g.total_hours, g.missed_hours,
            g.semester
        )
        analyses.append(a)
        
        # DB'ni yangilash: fail_risk va nb_warning
        async with AsyncSessionFactory() as db:
            await db.execute(
                update(Grade)
                .where(Grade.id == g.id)
                .values(fail_risk=a.fail_risk, nb_warning=a.nb_warning)
            )
            await db.commit()

    # GPA hisoblash
    gpa_vals = [a.total for a in analyses if a.total]
    gpa = round(sum(gpa_vals) / len(gpa_vals) / 25, 2) if gpa_vals else None

    return {
        "gpa": gpa,
        "semester": semester or "joriy",
        "profile": {
            "full_name": user.full_name or "",
            "group": "",
            "faculty": "",
            "semester": "",
            "gpa": gpa,
        },
        "grades": [
            {
                "subject": g.subject_name,
                "hemis_id": g.subject_hemis_id,
                "current": g.current_score,
                "midterm": g.midterm_score,
                "final": g.final_score,
                "total": a.total,
                "total_hours": g.total_hours,
                "missed": g.missed_hours,
                "fail_risk": a.fail_risk,  # ← DB'dan
                "nb_warning": a.nb_warning,  # ← DB'dan
                "needed_final": a.needed_final,
                "attendance": a.attendance_pct,
                "letter": a.letter,
            }
            for g, a in zip(grades, analyses)
        ],
    }


# /api/sync-data endpoint ni ham yangilash:

@app.post("/api/sync-data")
async def api_sync_data(body: dict):
    """
    local_sync.py dan keladigan ma'lumotlarni DB ga saqlaydi.
    Grade'ga fail_risk va nb_warning ham saqlaydi.
    """
    from database import Grade, Schedule, User
    from sqlalchemy import delete
    from analyzer import analyze
    
    telegram_id = body.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id kerak")

    async with AsyncSessionFactory() as db:
        # User
        res = await db.execute(select(User).where(User.id == telegram_id))
        user = res.scalars().first()
        if not user:
            user = User(id=telegram_id)
            db.add(user)

        profile = body.get("profile", {})
        if profile.get("full_name"):
            user.full_name = profile["full_name"]
        if profile.get("hemis_id"):
            user.hemis_id = profile["hemis_id"]
        user.is_demo = False

        # Grades + xavf hisoblash
        grades_data = body.get("grades", [])
        if grades_data:
            await db.execute(delete(Grade).where(Grade.user_id == telegram_id))
            await db.flush()
            
            for g in grades_data:
                # Analyzer qilish
                a = analyze(
                    g.get("subject", ""),
                    g.get("current"),
                    g.get("midterm"),
                    g.get("final"),
                    g.get("total_hours"),
                    g.get("missed"),
                    g.get("semester", "")
                )
                
                db.add(Grade(
                    user_id=telegram_id,
                    subject_name=g.get("subject", "")[:255],
                    subject_hemis_id=str(g.get("hemis_id", ""))[:63],
                    current_score=g.get("current"),
                    midterm_score=g.get("midterm"),
                    final_score=g.get("final"),
                    total_score=a.total,
                    total_hours=g.get("total_hours"),
                    missed_hours=g.get("missed") or 0,
                    fail_risk=a.fail_risk,  # ← Analizer'dan
                    nb_warning=a.nb_warning,  # ← Analizer'dan
                    needed_final=a.needed_final,
                    semester=str(g.get("semester", ""))[:15],
                ))

        # Schedule
        schedule = body.get("schedule", [])
        if schedule:
            await db.execute(delete(Schedule).where(Schedule.user_id == telegram_id))
            for s in schedule:
                db.add(Schedule(
                    user_id=telegram_id,
                    date=s.get("date", ""),
                    lesson_num=s.get("num", 1),
                    start_time=s.get("start", ""),
                    end_time=s.get("end", ""),
                    subject=s.get("subject", ""),
                    subject_type=s.get("s_type", ""),
                    teacher=s.get("teacher", ""),
                    room=s.get("room", ""),
                    building=s.get("building", ""),
                ))

        await db.commit()

    return {
        "success": True,
        "grades": len(grades_data),
        "schedule": len(schedule),
        "profile": profile.get("full_name", ""),
    }
