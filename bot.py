"""
bot.py - HELPER TDIU — To'liq bot handlerlari
"""
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from sqlalchemy import select

import config
from database import AsyncSessionFactory, User, SubscriptionTier

router = Router()

class HemisForm(StatesGroup):
    waiting_id       = State()
    waiting_password = State()
    waiting_captcha  = State()

# ── Klaviaturalar ─────────────────────────────────────────────

def kb(*rows):
    return InlineKeyboardMarkup(inline_keyboard=list(rows))

def btn(text, data=None, url=None, webapp=None):
    if webapp:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=webapp))
    if url:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=data)

def main_menu_kb(has_hemis=False, is_premium=False):
    rows = []
    if config.MINI_APP_URL:
        rows.append([btn("🚀 Mini App ni ochish", webapp=config.MINI_APP_URL)])
    if not has_hemis:
        rows.append([btn("🔗 Hemis ulash","connect_hemis"), btn("👀 Demo rejim","demo_mode")])
    rows.append([btn("📊 Baholar","show_grades"), btn("📅 Jadval","show_schedule")])
    if not is_premium:
        rows.append([btn("👑 Premium olish","buy_premium")])
    rows.append([btn("⚙️ Sozlamalar","settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ── /start — Onboarding ───────────────────────────────────────

WELCOME_NEW = """🎓 Assalomu alaykum, <b>{name}</b>! TDIU ga xush kelibsiz!

<b>HELPER TDIU</b> — sizning shaxsiy talaba yordamchingiz.

━━━━━━━━━━━━━━━━━━
📊 <b>Baholar</b> — Joriy, Oraliq, Yakuniy balllar grafik ko'rinishida
📅 <b>Jadval</b> — Haftalik dars jadvali
🔔 <b>Bildirishnoma</b> — Har kuni 20:00 da ertangi jadval
⚠️ <b>Xavf tahlili</b> — Qayta topshirish xavfini oldindan ko'ring
📍 <b>NB kuzatuvi</b> — 20% chegarasiga yaqinlashganda ogohlantirish
🗺️ <b>Navigator</b> — Auditoriyalar va o'qituvchilar joylashuvi
━━━━━━━━━━━━━━━━━━

<b>Boshlash uchun Hemis'ni ulang yoki Demo rejimni sinab ko'ring! 👇</b>"""

WELCOME_BACK = """🎓 Yana ko'rishdik, <b>{name}</b>!

HELPER TDIU tayyor. Nima qilmoqchisiz?"""

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    tg_id = msg.from_user.id

    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == tg_id))
        user = res.scalars().first()
        is_new = not user
        if is_new:
            user = User(
                id=tg_id,
                username=msg.from_user.username,
                full_name=msg.from_user.full_name,
                language_code=msg.from_user.language_code or "uz",
            )
            db.add(user)
            await db.commit()

    name      = msg.from_user.first_name or "Talaba"
    has_hemis = bool(user.hemis_id)
    is_prem   = user.tier == SubscriptionTier.PREMIUM

    text = (WELCOME_NEW if is_new else WELCOME_BACK).format(name=name)
    await msg.answer(text, reply_markup=main_menu_kb(has_hemis, is_prem))


@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "ℹ️ <b>HELPER TDIU — Yordam</b>\n\n"
        "/start — Bosh menyu\n"
        "/grades — Baholar\n"
        "/schedule — Bugungi jadval\n"
        "/profile — Profil\n"
        "/logout — Chiqish\n\n"
        "Muammo bo'lsa: @helper_tdiu_support"
    )


@router.message(Command("grades"))
async def cmd_grades(msg: Message):
    tg_id    = msg.from_user.id
    wait_msg = await msg.answer("⏳ Baholar yuklanmoqda...")

    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == tg_id))
        user = res.scalars().first()

    if not user or (not user.hemis_id and not user.is_demo):
        await wait_msg.edit_text(
            "❗ Avval Hemis'ni ulang yoki Demo rejimni tanlang.",
            reply_markup=kb([btn("🔗 Hemis ulash","connect_hemis"),
                             btn("👀 Demo","demo_mode")])
        )
        return

    from scraper import HemisScraper, HemisAuthError
    from analyzer import analyze, risk_text_uz
    try:
        async with HemisScraper(
            tg_id, user.hemis_id, user.hemis_password_enc, demo=user.is_demo
        ) as sc:
            await sc.ensure_login()
            grades = await sc.fetch_grades()

        lines     = ["📊 <b>Baholar</b>\n"]
        total_sum = 0
        count     = 0
        alerts    = []

        for g in grades:
            a   = analyze(g.subject, g.current, g.midterm, g.final,
                          g.total_hours, g.missed, g.semester)
            cur = str(int(g.current)) if g.current is not None else "—"
            mid = str(int(g.midterm)) if g.midterm is not None else "—"
            fin = str(int(g.final))   if g.final   is not None else "—"
            tot = str(round(a.total, 1)) if a.total is not None else "—"
            icon = "🔴" if a.fail_risk else ("🟡" if a.nb_warning else "🟢")
            letter = (" · " + a.letter) if a.letter else ""
            lines.append(
                icon + " <b>" + g.subject[:30] + "</b>\n"
                "   J:" + cur + "/20  O:" + mid + "/30  Y:" + fin + "/50\n"
                "   <b>Jami: " + tot + "</b>" + letter
            )
            if a.total: total_sum += a.total; count += 1
            rt = risk_text_uz(a)
            if rt: alerts.append(rt)

        if count:
            gpa = str(round(total_sum / count / 25, 2))
            lines.insert(1, "📈 <b>GPA:</b> " + gpa + "/4.0\n")

        text = "\n".join(lines)
        if alerts:
            text += "\n\n⚠️ <b>Ogohlantirishlar:</b>\n" + "\n".join(alerts)
        await wait_msg.edit_text(text[:4096])

    except HemisAuthError as e:
        await wait_msg.edit_text("❌ Hemis xatosi: " + str(e))
    except Exception as e:
        await wait_msg.edit_text("❌ Xato yuz berdi: " + str(e))


@router.message(Command("schedule"))
async def cmd_schedule(msg: Message):
    tg_id = msg.from_user.id
    wait  = await msg.answer("⏳ Jadval yuklanmoqda...")

    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == tg_id))
        user = res.scalars().first()

    if not user or (not user.hemis_id and not user.is_demo):
        await wait.edit_text(
            "❗ Avval Hemis'ni ulang.",
            reply_markup=kb([btn("🔗 Ulash","connect_hemis")])
        )
        return

    from scraper import HemisScraper
    from datetime import date
    DAYS = ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"]

    try:
        async with HemisScraper(
            tg_id, user.hemis_id, user.hemis_password_enc, demo=user.is_demo
        ) as sc:
            await sc.ensure_login()
            lessons = await sc.fetch_schedule(date.today())

        today_str = date.today().isoformat()
        today     = [l for l in lessons if l.date == today_str]
        day_name  = DAYS[date.today().weekday()]

        if not today:
            await wait.edit_text("📅 <b>" + day_name + "</b> — bugun darslar yo'q! 🎉")
            return

        lines = ["📅 <b>" + day_name + "</b>\n"]
        for l in sorted(today, key=lambda x: x.num):
            lines.append(
                "<b>" + str(l.num) + ". " + l.start + "–" + l.end + "</b>\n"
                "📚 " + l.subject + "\n"
                "📍 " + l.room + " · 👤 " + l.teacher
            )
        await wait.edit_text("\n\n".join(lines))
    except Exception as e:
        await wait.edit_text("❌ Xato: " + str(e))


@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    tg_id = msg.from_user.id
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == tg_id))
        user = res.scalars().first()
    if not user:
        await msg.answer("❗ /start ni bosing.")
        return
    tier  = "👑 Premium" if user.tier == SubscriptionTier.PREMIUM else "Bepul"
    mode  = "👀 Demo" if user.is_demo else ("🔗 Ulangan" if user.hemis_id else "❌ Ulanmagan")
    await msg.answer(
        "👤 <b>Profil</b>\n\n"
        "Ism: " + (user.full_name or "—") + "\n"
        "Hemis ID: " + (user.hemis_id or "—") + "\n"
        "Holat: " + mode + "\n"
        "Obuna: " + tier + "\n"
        "Bildirishnoma: " + ("✅" if user.notify_evening else "❌"),
        reply_markup=kb([btn("🚪 Chiqish","logout")])
    )


@router.message(Command("logout"))
async def cmd_logout(msg: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == msg.from_user.id))
        user = res.scalars().first()
        if user:
            user.hemis_id = None
            user.hemis_password_enc = None
            user.is_demo = False
            await db.commit()
    await msg.answer("✅ Chiqildi. /start")

# ── Callbacks ─────────────────────────────────────────────────

@router.callback_query(F.data == "show_grades")
async def cq_grades(cq: CallbackQuery):
    await cq.answer()
    await cmd_grades(cq.message)

@router.callback_query(F.data == "show_schedule")
async def cq_schedule(cq: CallbackQuery):
    await cq.answer()
    await cmd_schedule(cq.message)

@router.callback_query(F.data == "connect_hemis")
async def cq_connect(cq: CallbackQuery, state: FSMContext):
    await state.set_state(HemisForm.waiting_id)
    await cq.message.answer(
        "🔗 <b>Hemis ulash</b>\n\n"
        "Hemis ID ingizni kiriting:\n"
        "<i>Misol: U2200001</i>\n\n"
        "🔐 Parolingiz AES-256 bilan xavfsiz shifrlanadi."
    )
    await cq.answer()

@router.callback_query(F.data == "demo_mode")
async def cq_demo(cq: CallbackQuery):
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == cq.from_user.id))
        user = res.scalars().first()
        if user:
            user.is_demo = True
            await db.commit()
    await cq.message.answer(
        "👀 <b>Demo rejim yoqildi!</b>\n\n"
        "Namunali ma'lumotlar bilan ishlayapsiz.\n\n"
        "📊 /grades · 📅 /schedule · 👤 /profile"
    )
    await cq.answer("Demo yoqildi ✅")

@router.callback_query(F.data == "buy_premium")
async def cq_premium(cq: CallbackQuery):
    await cq.message.answer(
        "👑 <b>HELPER TDIU Premium</b>\n\n"
        "💰 <b>5,000 so'm / oy</b>\n\n"
        "✅ Darhol ball yangilanishi — balllaringiz o'zgarganda bildirishnoma\n"
        "✅ Jadval o'zgarish ogohlantirishlari\n"
        "✅ To'liq GPA analitika va prognoz\n"
        "✅ Maqsad ball hisob-kitobi\n"
        "✅ O'qituvchi real-time tracker\n"
        "✅ Reklamasiz interfeys\n\n"
        "📲 To'lov tizimi tez kunda ulash rejalashtirilgan!\n"
        "Xabardor bo'lish uchun kuting."
    )
    await cq.answer()

@router.callback_query(F.data == "settings")
async def cq_settings(cq: CallbackQuery):
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == cq.from_user.id))
        user = res.scalars().first()
    notif = user.notify_evening if user else True
    await cq.message.answer(
        "⚙️ <b>Sozlamalar</b>",
        reply_markup=kb(
            [btn("🔔 Kechki bildirishnoma: " + ("✅" if notif else "❌"), "toggle_notify")],
            [btn("🗑️ Hemis ma'lumotlarini o'chirish", "logout")],
        )
    )
    await cq.answer()

@router.callback_query(F.data == "toggle_notify")
async def cq_toggle(cq: CallbackQuery):
    new_st = True
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == cq.from_user.id))
        user = res.scalars().first()
        if user:
            user.notify_evening = not user.notify_evening
            new_st = user.notify_evening
            await db.commit()
    await cq.answer("Bildirishnoma " + ("yoqildi ✅" if new_st else "o'chirildi ❌"))

@router.callback_query(F.data == "logout")
async def cq_logout(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == cq.from_user.id))
        user = res.scalars().first()
        if user:
            user.hemis_id = None
            user.hemis_password_enc = None
            user.is_demo = False
            await db.commit()
    await cq.message.answer("✅ Ma'lumotlar o'chirildi. /start")
    await cq.answer()

# ── FSM ───────────────────────────────────────────────────────

@router.message(HemisForm.waiting_id)
async def fsm_id(msg: Message, state: FSMContext):
    hemis_id = msg.text.strip() if msg.text else ""
    if len(hemis_id) < 3:
        await msg.answer("❗ Hemis ID noto'g'ri. Qaytadan kiriting:")
        return
    await state.update_data(hemis_id=hemis_id)
    await state.set_state(HemisForm.waiting_password)
    await msg.answer(
        "✅ Hemis ID: <b>" + hemis_id + "</b>\n\n"
        "Endi parolingizni kiriting:\n"
        "<i>(Xabar avtomatik o'chiriladi)</i>"
    )

@router.message(HemisForm.waiting_password)
async def fsm_password(msg: Message, state: FSMContext):
    password = msg.text or ""
    data     = await state.get_data()
    hemis_id = data.get("hemis_id", "")
    try: await msg.delete()
    except: pass
    wait = await msg.answer("⏳ Captcha yuklanmoqda...")

    from scraper import HemisScraper, HemisAuthError
    from crypto import encrypt
    enc_pass = encrypt(password)

    # Captcha rasmini olamiz
    try:
        async with HemisScraper(msg.from_user.id, hemis_id, enc_pass) as sc:
            captcha_info = await sc.fetch_captcha()
    except Exception as e:
        await state.clear()
        await wait.edit_text(f"❌ Hemis ga ulanib bo'lmadi: {e}\n\nQaytadan /start")
        return

    if captcha_info and captcha_info.get("image"):
        # Captcha rasmini yuboramiz
        import io
        from aiogram.types import BufferedInputFile
        img_bytes = captcha_info["image"]
        await wait.delete()
        cap_msg = await msg.answer_photo(
            BufferedInputFile(img_bytes, filename="captcha.png"),
            caption="🔐 <b>Captcha kiriting:</b>\nRasmdagi matnni yozing:"
        )
        await state.update_data(
            hemis_id=hemis_id,
            enc_pass=enc_pass,
            captcha_field=captcha_info.get("field", ""),
            captcha_msg_id=cap_msg.message_id,
        )
        await state.set_state(HemisForm.waiting_captcha)
    else:
        # Captcha yo'q — to'g'ridan login
        await _do_login(msg, state, wait, hemis_id, enc_pass, captcha_text="")


@router.message(HemisForm.waiting_captcha)
async def fsm_captcha(msg: Message, state: FSMContext):
    captcha_text = msg.text.strip() if msg.text else ""
    data = await state.get_data()
    hemis_id     = data.get("hemis_id", "")
    enc_pass     = data.get("enc_pass", "")

    # Eski captcha rasmini o'chiramiz
    try:
        cap_id = data.get("captcha_msg_id")
        if cap_id:
            await msg.bot.delete_message(msg.chat.id, cap_id)
    except: pass

    wait = await msg.answer("⏳ Hemis'ga ulanilmoqda...")
    await _do_login(msg, state, wait, hemis_id, enc_pass, captcha_text)


async def _do_login(msg, state, wait_msg, hemis_id, enc_pass, captcha_text):
    from scraper import HemisScraper, HemisAuthError

    try:
        async with HemisScraper(msg.from_user.id, hemis_id, enc_pass) as sc:
            await sc.ensure_login(captcha_answer=captcha_text)

        async with AsyncSessionFactory() as db:
            res  = await db.execute(select(User).where(User.id == msg.from_user.id))
            user = res.scalars().first()
            if not user:
                user = User(id=msg.from_user.id)
                db.add(user)
            user.hemis_id = hemis_id
            user.hemis_password_enc = enc_pass
            user.is_demo = False
            await db.commit()

        await state.clear()
        await wait_msg.edit_text(
            "✅ <b>Hemis muvaffaqiyatli ulandi!</b>\n\n"
            "📊 /grades — Baholar\n"
            "📅 /schedule — Bugungi jadval\n"
            "👤 /profile — Profil\n\n"
            "Yoki Mini App ni oching! 🚀"
        )
    except HemisAuthError as e:
        await state.clear()
        await wait_msg.edit_text("❌ " + str(e) + "\n\nQaytadan /start")
    except Exception as e:
        await state.clear()
        await wait.edit_text("❌ Ulanib bo'lmadi: " + str(e))

# ── Create bot ────────────────────────────────────────────────

def create_bot():
    return Bot(token=config.BOT_TOKEN,
               default=DefaultBotProperties(parse_mode=ParseMode.HTML))

def create_dispatcher():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp

async def start_bot():
    if not config.BOT_TOKEN:
        print("BOT_TOKEN yo'q!")
        return
    bot = create_bot()
    dp  = create_dispatcher()
    print("Bot polling boshlandi...")
    await dp.start_polling(bot, allowed_updates=["message","callback_query"])
