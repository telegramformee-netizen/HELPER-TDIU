"""
bot.py - aiogram 3.x bot: barcha handlerlar
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

# FSM
class HemisForm(StatesGroup):
    waiting_id       = State()
    waiting_password = State()

# Klaviaturalar
def main_keyboard(has_hemis=False):
    btns = [[
        InlineKeyboardButton(
            text="🚀 Mini App ochish",
            web_app=WebAppInfo(url=config.MINI_APP_URL)
        )
    ]]
    if not has_hemis:
        btns.append([
            InlineKeyboardButton(text="🔗 Hemis ulash",  callback_data="connect_hemis"),
            InlineKeyboardButton(text="👀 Demo rejim",   callback_data="demo_mode"),
        ])
    btns.append([
        InlineKeyboardButton(text="👑 Premium olish", callback_data="buy_premium"),
        InlineKeyboardButton(text="⚙️ Sozlamalar",    callback_data="settings"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=btns)

# /start
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    tg_id = msg.from_user.id

    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == tg_id))
        user = res.scalars().first()
        if not user:
            user = User(
                id=tg_id,
                username=msg.from_user.username,
                full_name=msg.from_user.full_name,
                language_code=msg.from_user.language_code or "uz",
            )
            db.add(user)
            await db.commit()

    name      = msg.from_user.first_name or "Talaba"
    has_hemis = bool(user and user.hemis_id)
    is_premium = user and user.tier == SubscriptionTier.PREMIUM

    if is_premium:
        tier_line = "👑 <b>Premium foydalanuvchi</b>"
    else:
        tier_line = "💡 <b>Bepul rejim</b> — Premium: 5,000 so'm/oy"

    text = (
        "🎓 Assalomu alaykum, <b>" + name + "</b>!\n\n"
        "<b>HELPER TDIU</b> — TDIU talabalari uchun aqlli yordamchi!\n\n"
        "📊 Baholar va GPA tahlili\n"
        "📅 Haftalik dars jadvali\n"
        "🔔 Har kuni 20:00 da ertangi jadval\n"
        "⚠️ Qayta topshirish xavfi ogohlantirishi\n"
        "📍 NB chegarasi kuzatuvi\n"
        "🗺️ Auditoriya navigatori\n\n"
        + tier_line + "\n\n"
        "👇 Boshlash uchun:"
    )
    await msg.answer(text, reply_markup=main_keyboard(has_hemis))

# /help
@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "ℹ️ <b>HELPER TDIU — Yordam</b>\n\n"
        "/start — Bosh menyu\n"
        "/help — Yordam\n"
        "/grades — Baholar\n"
        "/schedule — Bugungi jadval\n"
        "/profile — Profil\n"
        "/logout — Chiqish"
    )

# /grades
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
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔗 Hemis ulash", callback_data="connect_hemis"),
                InlineKeyboardButton(text="👀 Demo",        callback_data="demo_mode"),
            ]])
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
            tot = round(a.total, 1)   if a.total   is not None else 0

            if a.fail_risk:
                icon = "🔴"
            elif a.nb_warning:
                icon = "🟡"
            else:
                icon = "🟢"

            letter = (" · " + a.letter) if a.letter else ""
            lines.append(
                icon + " <b>" + g.subject[:28] + "</b>\n"
                "   Joriy: " + cur + "/20 · Oraliq: " + mid + "/30 · Yakuniy: " + fin + "/50\n"
                "   <b>Jami: " + str(tot) + "</b>" + letter
            )

            if a.total:
                total_sum += a.total
                count += 1

            rt = risk_text_uz(a)
            if rt:
                alerts.append(rt)

        if count:
            gpa = round(total_sum / count / 25, 2)
            lines.insert(1, "📈 <b>GPA:</b> " + str(gpa) + "/4.0\n")

        text = "\n".join(lines)
        if alerts:
            text += "\n\n⚠️ <b>Ogohlantirishlar:</b>\n" + "\n".join(alerts)

        await wait_msg.edit_text(text[:4096])

    except HemisAuthError as e:
        await wait_msg.edit_text("❌ Hemis xatosi: " + str(e) + "\n\nQayta: /start")
    except Exception as e:
        await wait_msg.edit_text("❌ Xato: " + str(e))

# /schedule
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
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔗 Ulash", callback_data="connect_hemis")
            ]])
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

        lines = ["📅 <b>Bugungi jadval — " + day_name + "</b>\n"]
        for l in sorted(today, key=lambda x: x.num):
            lines.append(
                "<b>" + str(l.num) + ". " + l.start + "–" + l.end + "</b>\n"
                "📚 " + l.subject + "\n"
                "📍 " + l.room + " (" + l.building + ") · 👤 " + l.teacher + "\n"
                "🏷 " + l.s_type
            )

        await wait.edit_text("\n\n".join(lines))

    except Exception as e:
        await wait.edit_text("❌ Xato: " + str(e))

# /profile
@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    tg_id = msg.from_user.id
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == tg_id))
        user = res.scalars().first()

    if not user:
        await msg.answer("❗ Avval /start ni bosing.")
        return

    tier = "👑 Premium" if user.tier == SubscriptionTier.PREMIUM else "Bepul"
    if user.is_demo:
        mode = "👀 Demo"
    elif user.hemis_id:
        mode = "🔗 Hemis ulangan"
    else:
        mode = "❌ Ulanmagan"

    notif = "✅" if user.notify_evening else "❌"
    await msg.answer(
        "👤 <b>Profil</b>\n\n"
        "Telegram: " + (user.full_name or "—") + "\n"
        "Hemis ID: " + (user.hemis_id or "—") + "\n"
        "Rejim: " + mode + "\n"
        "Obuna: " + tier + "\n"
        "Bildirishnoma: " + notif,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚪 Chiqish", callback_data="logout")
        ]])
    )

# /logout
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
    await msg.answer("✅ Ma'lumotlar o'chirildi. Qayta: /start")

# Callbacks
@router.callback_query(F.data == "connect_hemis")
async def cq_connect(cq: CallbackQuery, state: FSMContext):
    await state.set_state(HemisForm.waiting_id)
    await cq.message.answer(
        "🔗 <b>Hemis'ni ulash</b>\n\n"
        "Hemis ID ingizni kiriting (masalan: U2200001):\n\n"
        "🔐 Parolingiz AES-256 bilan shifrlanadi."
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
        "Namunali ma'lumotlar ko'rsatiladi.\n\n"
        "Buyruqlar: /grades · /schedule · /profile"
    )
    await cq.answer("Demo rejim yoqildi")

@router.callback_query(F.data == "buy_premium")
async def cq_premium(cq: CallbackQuery):
    await cq.message.answer(
        "👑 <b>Premium obuna</b>\n\n"
        "💰 Narxi: <b>5,000 so'm / oy</b>\n\n"
        "✅ Darhol ball yangilanishi\n"
        "✅ Jadval o'zgarish ogohlantirishlari\n"
        "✅ To'liq GPA analitika\n"
        "✅ O'qituvchi tracker\n"
        "✅ Reklamasiz interfeys\n\n"
        "📲 To'lov tizimi tez kunda ulash rejalashtirilgan!"
    )
    await cq.answer()

@router.callback_query(F.data == "settings")
async def cq_settings(cq: CallbackQuery):
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == cq.from_user.id))
        user = res.scalars().first()
    notif = user.notify_evening if user else True
    notif_text = "✅" if notif else "❌"
    await cq.message.answer(
        "⚙️ <b>Sozlamalar</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🔔 Kechki bildirishnoma: " + notif_text,
                callback_data="toggle_notify"
            )
        ], [
            InlineKeyboardButton(text="🚪 Chiqish", callback_data="logout")
        ]])
    )
    await cq.answer()

@router.callback_query(F.data == "toggle_notify")
async def cq_toggle(cq: CallbackQuery):
    async with AsyncSessionFactory() as db:
        res  = await db.execute(select(User).where(User.id == cq.from_user.id))
        user = res.scalars().first()
        if user:
            user.notify_evening = not user.notify_evening
            state = user.notify_evening
            await db.commit()
    msg = "Yoqildi ✅" if state else "O'chirildi ❌"
    await cq.answer("Bildirishnoma " + msg)

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
    await cq.message.answer("✅ Chiqildi. Qayta: /start")
    await cq.answer()

# FSM: Hemis ID
@router.message(HemisForm.waiting_id)
async def fsm_id(msg: Message, state: FSMContext):
    hemis_id = msg.text.strip()
    if len(hemis_id) < 3:
        await msg.answer("❗ Hemis ID juda qisqa. Qaytadan:")
        return
    await state.update_data(hemis_id=hemis_id)
    await state.set_state(HemisForm.waiting_password)
    await msg.answer(
        "✅ Hemis ID: <b>" + hemis_id + "</b>\n\n"
        "Endi parolingizni kiriting:\n"
        "(Xabar avtomatik o'chiriladi)"
    )

# FSM: Parol
@router.message(HemisForm.waiting_password)
async def fsm_password(msg: Message, state: FSMContext):
    password = msg.text
    data     = await state.get_data()
    hemis_id = data.get("hemis_id", "")

    try:
        await msg.delete()
    except Exception:
        pass

    wait = await msg.answer("⏳ Hemis'ga ulanilmoqda...")

    from scraper import HemisScraper, HemisAuthError
    from crypto import encrypt

    enc_pass = encrypt(password)

    try:
        async with HemisScraper(msg.from_user.id, hemis_id, enc_pass) as sc:
            await sc.ensure_login()

        async with AsyncSessionFactory() as db:
            res  = await db.execute(select(User).where(User.id == msg.from_user.id))
            user = res.scalars().first()
            if user:
                user.hemis_id = hemis_id
                user.hemis_password_enc = enc_pass
                user.is_demo = False
                await db.commit()

        await state.clear()
        await wait.edit_text(
            "✅ <b>Hemis muvaffaqiyatli ulandi!</b>\n\n"
            "Buyruqlar:\n"
            "📊 /grades — Baholar\n"
            "📅 /schedule — Bugungi jadval\n"
            "👤 /profile — Profil"
        )

    except HemisAuthError as e:
        await state.clear()
        await wait.edit_text("❌ Xato: " + str(e) + "\n\nQaytadan: /start")
    except Exception as e:
        await state.clear()
        await wait.edit_text("❌ Ulanib bo'lmadi: " + str(e) + "\n\nQaytadan: /start")

# Bot yaratish
def create_bot():
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

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
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
