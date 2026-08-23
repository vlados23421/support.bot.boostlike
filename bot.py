import asyncio
import logging
import os
import csv
from io import StringIO
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from database import Database
from emoji import Emoji
import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# --- Состояния ---
class SupportState(StatesGroup):
    waiting_problem = State()

# --- Клавиатуры ---

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Создать заявку",
                callback_data="ticket",
                icon_custom_emoji_id=Emoji.SHIELD
            )],
            [InlineKeyboardButton(
                text="Курс монет",
                callback_data="rate",
                icon_custom_emoji_id=Emoji.STAR
            )],
            [InlineKeyboardButton(
                text="Частые вопросы",
                callback_data="faq",
                icon_custom_emoji_id=Emoji.DIAMOND
            )],
            [InlineKeyboardButton(
                text="Связаться с оператором",
                callback_data="operator",
                icon_custom_emoji_id=Emoji.ROCKET
            )],
            [InlineKeyboardButton(
                text="📖 Инструкция",
                callback_data="guide",
                icon_custom_emoji_id=Emoji.DIAMOND
            )]
        ]
    )

def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Назад",
                callback_data="back",
                icon_custom_emoji_id=Emoji.SHIELD
            )]
        ]
    )

def faq_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Как пополнить баланс?",
                callback_data="faq_0",
                icon_custom_emoji_id=Emoji.STAR
            )],
            [InlineKeyboardButton(
                text="Какие пакеты есть?",
                callback_data="faq_1",
                icon_custom_emoji_id=Emoji.DIAMOND
            )],
            [InlineKeyboardButton(
                text="Как создать задание?",
                callback_data="faq_2",
                icon_custom_emoji_id=Emoji.ROCKET
            )],
            [InlineKeyboardButton(
                text="Почему задержка?",
                callback_data="faq_3",
                icon_custom_emoji_id=Emoji.FIRE
            )],
            [InlineKeyboardButton(
                text="Назад",
                callback_data="back",
                icon_custom_emoji_id=Emoji.SHIELD
            )]
        ]
    )

def rate_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 1", callback_data="rate_1"),
                InlineKeyboardButton(text="⭐ 2", callback_data="rate_2"),
                InlineKeyboardButton(text="⭐ 3", callback_data="rate_3"),
                InlineKeyboardButton(text="⭐ 4", callback_data="rate_4"),
                InlineKeyboardButton(text="⭐ 5", callback_data="rate_5")
            ]
        ]
    )

# --- FAQ ---

FAQ = {
    "Как пополнить баланс?": 
        "⭐ **Пополнение баланса:**\n\n"
        "Ты можешь пополнить баланс двумя способами:\n"
        "• ⭐ **Звёзды Telegram** — покупай внутри бота\n"
        "• 💎 **Криптовалюта** — перевод на наш кошелёк\n\n"
        "Минимальная сумма пополнения: 1 ⭐ или 1.5 ₽",
    
    "Какие пакеты есть?": 
        "💎 **Пакеты монет:**\n\n"
        "⭐ **За звёзды:**\n"
        "• 1 ⭐ → 150 монет\n"
        "• 5 ⭐ → 825 монет\n"
        "• 10 ⭐ → 1 800 монет\n"
        "• 25 ⭐ → 4 500 монет\n"
        "• 50 ⭐ → 9 750 монет\n"
        "• 75 ⭐ → 15 750 монет\n"
        "• 100 ⭐ → 21 000 монет\n\n"
        "💎 **За крипту:**\n"
        "• 1.5 ₽ → 450 монет\n"
        "• 7.5 ₽ → 2 250 монет\n"
        "• 15 ₽ → 4 500 монет\n"
        "• 38 ₽ → 11 400 монет\n\n"
        "🔥 **Бонус!** 100 звёзд дают на 40% больше!",
    
    "Как создать задание?": 
        "🚀 **Создание задания:**\n\n"
        "1. Перейди на наш сайт\n"
        "2. Вставь ссылку на пост\n"
        "3. Укажи количество лайков\n"
        "4. Подтверди заказ\n\n"
        "🛡️ Лайки начисляются в течение 5-30 минут.",
    
    "Почему задержка?": 
        "🔥 **Почему лайки идут долго?**\n\n"
        "Наши боты работают в несколько потоков,\n"
        "чтобы избежать блокировок.\n\n"
        "• Обычно: 5-30 минут\n"
        "• В пиковые часы: до 1 часа\n\n"
        "🎉 Если прошло больше часа — создай заявку!"
}

# --- Автоответы ---

AUTO_REPLIES = {
    "курс": "💱 Узнать курс монет можно по команде /rate",
    "монет": "💱 Узнать курс монет можно по команде /rate",
    "заявк": "📝 Создать заявку можно через /start → Создать заявку",
    "помощ": "📝 Создай заявку через /start → Создать заявку",
    "привет": "👋 Привет! Чем могу помочь? Нажми /start",
    "здравствуй": "👋 Здравствуйте! Чем могу помочь?",
    "спасибо": "🙌 Пожалуйста! Обращайтесь ещё!",
    "проблем": "🛡️ Опиши проблему в заявке через /start → Создать заявку",
    "баг": "🐛 Опиши баг в заявке, мы всё исправим!",
    "не работает": "🔧 Создай заявку, мы проверим!",
    "инструкц": "📖 Инструкция: /start → Частые вопросы → Как создать задание?"
}

# ==================== УЛУЧШЕНИЯ ====================

# --- 2. РАССЫЛКА ВСЕМ ПОЛЬЗОВАТЕЛЯМ ---

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    text = " ".join(message.text.split()[1:])
    if not text:
        await message.answer("❌ Использование: /broadcast <текст сообщения>")
        return
    
    users = db.get_all_users()
    success = 0
    failed = 0
    
    status_msg = await message.answer("⏳ Отправляю рассылку...")
    
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 {text}")
            success += 1
            await asyncio.sleep(0.05)  # Чтобы не заблокировали
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ Рассылка завершена!\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Не доставлено: {failed}"
    )

# --- 4. ПОИСК ЗАЯВОК ---

@dp.message(Command("find"))
async def find_ticket(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    query = " ".join(message.text.split()[1:])
    if not query:
        await message.answer("❌ Использование: /find <текст или ID>")
        return
    
    # Поиск по ID
    if query.isdigit():
        ticket = db.get_ticket_by_id(int(query))
        if ticket:
            await message.answer(
                f"✅ **Заявка #{ticket[0]}**\n\n"
                f"👤 @{ticket[2]}\n"
                f"📝 {ticket[3]}\n"
                f"📌 Статус: {ticket[4]}\n"
                f"📅 {ticket[5]}",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Заявка не найдена")
        return
    
    # Поиск по тексту
    tickets = db.search_tickets(query)
    if not tickets:
        await message.answer("❌ Ничего не найдено")
        return
    
    text = f"🔍 Найдено {len(tickets)} заявок:\n\n"
    for ticket in tickets[:5]:
        text += f"#{ticket[0]} — @{ticket[2]} — {ticket[3][:50]}...\n"
    
    if len(tickets) > 5:
        text += f"\n... и ещё {len(tickets) - 5}"
    
    await message.answer(text)

# --- 5. ОГРАНИЧЕНИЕ НА ЗАЯВКИ В ДЕНЬ ---

async def check_daily_limit(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    count = db.get_user_tickets_count(user_id, today)
    return count < 5  # Максимум 5 заявок в день

# --- 6. ИНТЕРАКТИВНЫЕ КНОПКИ С ПАГИНАЦИЕЙ ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    tickets = db.get_tickets()
    if not tickets:
        await message.answer("📭 Нет открытых заявок")
        return
    
    await show_tickets_page(message, tickets, 0)

async def show_tickets_page(message, tickets, page):
    page_size = 3
    total_pages = (len(tickets) + page_size - 1) // page_size
    
    if page < 0 or page >= total_pages:
        return
    
    start = page * page_size
    end = min(start + page_size, len(tickets))
    
    text = f"📋 **Заявки (стр. {page + 1}/{total_pages})**\n\n"
    for ticket in tickets[start:end]:
        status_emoji = "🟡" if ticket[4] == "Новая" else "🟠" if ticket[4] == "В работе" else "🟢"
        text += f"{status_emoji} #{ticket[0]} — @{ticket[2]}\n📝 {ticket[3][:50]}...\n\n"
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("⬅️", callback_data=f"admin_page_{page-1}"),
                InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="none"),
                InlineKeyboardButton("➡️", callback_data=f"admin_page_{page+1}")
            ],
            [
                InlineKeyboardButton("📥 Экспорт CSV", callback_data="export_csv")
            ]
        ]
    )
    
    if hasattr(message, 'edit_text'):
        await message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("admin_page_"))
async def admin_page_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    page = int(callback.data.split("_")[2])
    tickets = db.get_tickets()
    await show_tickets_page(callback.message, tickets, page)
    await callback.answer()

# --- 7. ВИЗУАЛЬНЫЙ СТАТУС В ЗАЯВКАХ ---

STATUS_EMOJI = {
    "Новая": "🟡",
    "В работе": "🟠",
    "Закрыта": "🟢"
}

# --- 8. ЗВУКОВЫЕ УВЕДОМЛЕНИЯ ---

async def send_notification_with_sound(admin_id, text):
    try:
        await bot.send_audio(
            admin_id,
            audio="https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a0c8c8.mp3",
            caption=text,
            parse_mode="Markdown"
        )
    except:
        await bot.send_message(admin_id, text, parse_mode="Markdown")

# --- 9. ДАШБОРД В ВИДЕ КАРТИНКИ ---

@dp.message(Command("dashboard"))
async def dashboard(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    stats = db.get_stats()
    
    # Создаём текстовый дашборд
    text = (
        f"📊 **ДАШБОРД ПОДДЕРЖКИ**\n\n"
        f"📌 Всего заявок: {stats['total_tickets']}\n"
        f"🟡 Открытых: {stats['open_tickets']}\n"
        f"🟢 Закрытых: {stats['closed_tickets']}\n"
        f"⭐ Средняя оценка: {stats['avg_rating']:.1f}/5\n"
        f"👤 Пользователей: {stats['total_users']}\n"
        f"⏱ Среднее время ответа: {stats['avg_response_time']:.0f} мин"
    )
    
    # Простая ASCII-диаграмма
    total = stats['total_tickets'] or 1
    open_bar = "█" * int((stats['open_tickets'] / total) * 20)
    closed_bar = "█" * int((stats['closed_tickets'] / total) * 20)
    
    text += f"\n\n📈 **Статус заявок:**\n"
    text += f"🟡 Открыто: {open_bar} {stats['open_tickets']}\n"
    text += f"🟢 Закрыто: {closed_bar} {stats['closed_tickets']}"
    
    await message.answer(text, parse_mode="Markdown")

# --- 10. НОЧНОЙ РЕЖИМ ---

def is_night():
    hour = datetime.now().hour
    return hour < 8 or hour > 23

# --- 12. БЛОКИРОВКА СПАМЕРОВ ---

@dp.message(Command("block"))
async def block_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    try:
        user_id = int(message.text.split()[1])
        db.block_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} заблокирован")
    except:
        await message.answer("❌ Использование: /block <user_id>")

@dp.message(Command("unblock"))
async def unblock_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    try:
        user_id = int(message.text.split()[1])
        db.unblock_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} разблокирован")
    except:
        await message.answer("❌ Использование: /unblock <user_id>")

# --- 11. ЭКСПОРТ CSV ---

@dp.callback_query(F.data == "export_csv")
async def export_csv_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    await export_csv(callback.message)
    await callback.answer()

@dp.message(Command("export"))
async def export_csv_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    await export_csv(message)

async def export_csv(message):
    tickets = db.get_all_tickets()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Дата", "Пользователь", "Текст", "Статус", "Ответ", "Дата закрытия", "Оценка"])
    
    for ticket in tickets:
        writer.writerow([
            ticket[0], ticket[4], ticket[2], 
            ticket[3][:200], ticket[5], ticket[6] or "", 
            ticket[7] or "", ticket[8] or ""
        ])
    
    await message.answer_document(
        document=output.getvalue().encode(),
        filename=f"tickets_{datetime.now().strftime('%Y%m%d')}.csv"
    )

# --- ОСНОВНЫЕ ОБРАБОТЧИКИ (С УЛУЧШЕНИЯМИ) ---

@dp.message(Command("start"))
async def start(message: types.Message):
    # Проверка на блокировку
    if db.is_user_blocked(message.from_user.id):
        await message.answer("⛔ Вы заблокированы. Обратитесь к администратору.")
        return
    
    await message.answer(
        "🎉 **Привет!**\n\n"
        "Я бот поддержки **BoostSocialLikeBot**.\n\n"
        "Здесь ты можешь:\n"
        "🛡️ Создать заявку в поддержку\n"
        "⭐ Узнать курс монет\n"
        "💎 Получить ответы на вопросы\n"
        "🚀 Связаться с оператором\n"
        "📖 Изучить инструкции\n\n"
        "Выбери действие ниже 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "back")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🎉 **Главное меню**\n\n"
        "Выбери действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await callback.answer()

# --- АВТООТВЕТЫ ---

@dp.message()
async def auto_reply(message: types.Message):
    if message.text is None or message.text.startswith('/'):
        return
    
    # Проверка на блокировку
    if db.is_user_blocked(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    
    text = message.text.lower()
    
    for word, reply in AUTO_REPLIES.items():
        if word in text:
            await message.answer(reply)
            break

# --- ЗАЯВКИ (С ОГРАНИЧЕНИЕМ И УДАЛЕНИЕМ) ---

@dp.callback_query(F.data == "ticket")
async def create_ticket(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    
    # Проверка на блокировку
    if db.is_user_blocked(callback.from_user.id):
        await callback.message.answer("⛔ Вы заблокированы.")
        await callback.answer()
        return
    
    # Проверка дневного лимита
    if not await check_daily_limit(callback.from_user.id):
        await callback.message.answer(
            "❌ Вы создали максимальное количество заявок на сегодня (5).\n"
            "Попробуйте завтра."
        )
        await callback.answer()
        return
    
    msg = await callback.message.answer(
        "🛡️ **Опиши свою проблему подробно:**\n\n"
        "Ты можешь также отправить скриншот 📸\n\n"
        "Укажи, пожалуйста:\n"
        "• ID заказа (если есть)\n"
        "• Что случилось\n"
        "• Когда это произошло\n\n"
        "🚀 Оператор ответит в ближайшее время ⏳",
        parse_mode="Markdown"
    )
    await state.update_data(last_message_id=msg.message_id)
    await state.set_state(SupportState.waiting_problem)
    await callback.answer()

@dp.message(SupportState.waiting_problem, F.photo)
async def save_ticket_with_photo(message: types.Message, state: FSMContext):
    # Проверка на блокировку
    if db.is_user_blocked(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    
    data = await state.get_data()
    if "last_message_id" in data:
        try:
            await message.bot.delete_message(message.chat.id, data["last_message_id"])
        except:
            pass
    
    photo = await message.photo[-1].download()
    photo_path = photo.name
    
    ticket_id = db.add_ticket(
        message.from_user.id,
        message.from_user.username or "без username",
        f"[Фото] {message.caption or 'Без описания'}"
    )
    
    # Удаляем сообщение пользователя
    await message.delete()
    
    # Ночной режим
    if is_night():
        await message.answer(
            "🌙 **Заявка принята!**\n\n"
            "Оператор ответит утром. Спасибо за понимание! 🎉",
            parse_mode="Markdown",
            reply_markup=back_menu()
        )
    else:
        await message.answer(
            f"🎉 **Заявка #{ticket_id} создана!**\n\n"
            "🚀 Оператор свяжется с тобой в ближайшее время.\n"
            "🛡️ Ожидай ответа в этом чате 📩",
            parse_mode="Markdown",
            reply_markup=back_menu()
        )
    
    await state.clear()
    
    user_link = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    caption = (
        f"🔥 **Новая заявка #{ticket_id} с фото**\n\n"
        f"👤 {user_link}\n"
        f"🆔 ID: {message.from_user.id}\n\n"
        f"📝 **Текст:**\n{message.caption or 'Без описания'}"
    )
    
    # Отправляем в канал
    with open(photo_path, 'rb') as photo_file:
        await bot.send_photo(
            CHANNEL_ID,
            photo_file,
            caption=caption,
            parse_mode="Markdown"
        )
    
    # Отправляем в ЛС админу со звуком
    await send_notification_with_sound(ADMIN_ID, caption)

@dp.message(SupportState.waiting_problem)
async def save_ticket(message: types.Message, state: FSMContext):
    # Проверка на блокировку
    if db.is_user_blocked(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    
    data = await state.get_data()
    if "last_message_id" in data:
        try:
            await message.bot.delete_message(message.chat.id, data["last_message_id"])
        except:
            pass
    
    ticket_id = db.add_ticket(
        message.from_user.id,
        message.from_user.username or "без username",
        message.text
    )
    
    # Удаляем сообщение пользователя
    await message.delete()
    
    # Ночной режим
    if is_night():
        await message.answer(
            "🌙 **Заявка принята!**\n\n"
            "Оператор ответит утром. Спасибо за понимание! 🎉",
            parse_mode="Markdown",
            reply_markup=back_menu()
        )
    else:
        await message.answer(
            f"🎉 **Заявка #{ticket_id} создана!**\n\n"
            "🚀 Оператор свяжется с тобой в ближайшее время.\n"
            "🛡️ Ожидай ответа в этом чате 📩",
            parse_mode="Markdown",
            reply_markup=back_menu()
        )
    
    await state.clear()
    
    user_link = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    caption = (
        f"🔥 **Новая заявка #{ticket_id}**\n\n"
        f"👤 {user_link}\n"
        f"🆔 ID: {message.from_user.id}\n\n"
        f"📝 **Текст:**\n{message.text[:500]}"
    )
    
    # Отправляем в канал
    await bot.send_message(
        CHANNEL_ID,
        caption,
        parse_mode="Markdown"
    )
    
    # Отправляем в ЛС админу со звуком
    await send_notification_with_sound(ADMIN_ID, caption)

# --- ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (КУРС, FAQ, ОПЕРАТОР) ---

@dp.callback_query(F.data == "rate")
async def show_rate(callback: CallbackQuery):
    await callback.message.delete()
    
    text = (
        "💎 **Курс монет**\n\n"
        "⭐ За 1 ⭐ — 150 монет\n"
        "💎 За 1 ₽ в крипте — 300 монет\n\n"
        "🎉 **Пакеты за звёзды:**\n"
        "• 1 ⭐ → 150 монет\n"
        "• 5 ⭐ → 825 монет\n"
        "• 10 ⭐ → 1 800 монет\n"
        "• 25 ⭐ → 4 500 монет\n"
        "• 50 ⭐ → 9 750 монет\n"
        "• 75 ⭐ → 15 750 монет\n"
        "• 100 ⭐ → 21 000 монет\n\n"
        "💎 **Пакеты за крипту:**\n"
        "• 1.5 ₽ → 450 монет\n"
        "• 7.5 ₽ → 2 250 монет\n"
        "• 15 ₽ → 4 500 монет\n"
        "• 38 ₽ → 11 400 монет\n\n"
        "🔥 **Бонус!** 100 звёзд дают на 40% больше!"
    )
    
    await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    await callback.message.delete()
    
    await callback.message.answer(
        "💎 **Часто задаваемые вопросы**\n\n"
        "Выбери интересующий вопрос 👇",
        parse_mode="Markdown",
        reply_markup=faq_menu()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("faq_"))
async def faq_answer(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    question = list(FAQ.keys())[index]
    answer = FAQ[question]
    
    await callback.message.delete()
    await callback.message.answer(
        f"**{question}**\n\n{answer}",
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "operator")
async def contact_operator(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🚀 **Связь с оператором**\n\n"
        "🛡️ Создай заявку через кнопку «Создать заявку».\n"
        "⭐ Оператор ответит в ближайшее время.\n\n"
        "📌 **Время ответа:**\n"
        "• В рабочее время: до 15 минут\n"
        "• Ночью: до 2 часов\n\n"
        "🎉 Спасибо за понимание! 🙏",
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "guide")
async def show_guide(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "📖 **Инструкция по созданию задания**\n\n"
        "1️⃣ Перейди на наш сайт\n"
        "2️⃣ Скопируй ссылку на пост\n"
        "3️⃣ Выбери количество лайков\n"
        "4️⃣ Оплати через звёзды или крипту\n"
        "5️⃣ Лайки начислятся через 5-30 минут\n\n"
        "🔥 **Совет:** Покупай пакеты от 100 звёзд — экономия 40%!",
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await callback.answer()

# --- ЗАПУСК ---

async def health_check(request):
    return web.Response(text="OK")

async def run_bot():
    await dp.start_polling(bot)

async def main():
    port = int(os.environ.get("PORT", 8080))
    
    app = web.Application()
    app.router.add_get('/health', health_check)
    
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logging.info(f"✅ Бот запущен на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
