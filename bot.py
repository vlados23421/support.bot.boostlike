import asyncio
import logging
import os
from datetime import datetime
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

# --- Обработчики ---

@dp.message(Command("start"))
async def start(message: types.Message):
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

# --- Автоответы ---

@dp.message()
async def auto_reply(message: types.Message):
    if message.text is None or message.text.startswith('/'):
        return
    
    text = message.text.lower()
    
    for word, reply in AUTO_REPLIES.items():
        if word in text:
            await message.answer(reply)
            break

# --- Заявки ---

@dp.callback_query(F.data == "ticket")
async def create_ticket(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
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
    
    await message.delete()
    
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
    
    # Отправляем в ЛС админу
    with open(photo_path, 'rb') as photo_file:
        await bot.send_photo(
            ADMIN_ID,
            photo_file,
            caption=caption,
            parse_mode="Markdown"
        )

@dp.message(SupportState.waiting_problem)
async def save_ticket(message: types.Message, state: FSMContext):
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
    
    await message.delete()
    
    await message.answer(
        "🎉 **Заявка #{ticket_id} создана!**\n\n"
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
    
    # Отправляем в ЛС админу
    await bot.send_message(
        ADMIN_ID,
        caption,
        parse_mode="Markdown"
    )

# --- Ответ пользователю ---

@dp.message(Command("reply"))
async def reply_to_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("❌ Использование: /reply <id> <текст ответа>")
            return
        
        ticket_id = int(parts[1])
        reply_text = parts[2]
        
        ticket = db.get_ticket_by_id(ticket_id)
        if not ticket:
            await message.answer(f"❌ Заявка #{ticket_id} не найдена")
            return
        
        await bot.send_message(
            ticket[1],
            f"📩 **Ответ оператора по заявке #{ticket_id}**\n\n"
            f"{reply_text}\n\n"
            f"🛡️ Если проблема решена, создайте новую заявку.",
            parse_mode="Markdown"
        )
        
        user_link = f"@{ticket[2]}" if ticket[2] else f"ID: {ticket[1]}"
        await bot.send_message(
            CHANNEL_ID,
            f"📩 **Ответ на заявку #{ticket_id}**\n\n"
            f"👤 {user_link}\n\n"
            f"📝 {reply_text}",
            parse_mode="Markdown"
        )
        
        await message.answer(f"✅ Ответ отправлен пользователю (заявка #{ticket_id})")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- Оценка поддержки ---

@dp.message(Command("close"))
async def close_ticket(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    try:
        ticket_id = int(message.text.split()[1])
        db.close_ticket(ticket_id)
        
        ticket = db.get_ticket_by_id(ticket_id)
        if ticket:
            await bot.send_message(
                ticket[1],
                f"✅ **Заявка #{ticket_id} закрыта!**\n\n"
                "Пожалуйста, оцени качество поддержки:",
                reply_markup=rate_keyboard()
            )
            
            user_link = f"@{ticket[2]}" if ticket[2] else f"ID: {ticket[1]}"
            await bot.send_message(
                CHANNEL_ID,
                f"✅ **Заявка #{ticket_id} закрыта**\n\n"
                f"👤 {user_link}",
                parse_mode="Markdown"
            )
        
        await message.answer(f"🎉 Заявка #{ticket_id} закрыта")
        
    except:
        await message.answer("❌ Использование: /close <id>")

@dp.callback_query(F.data.startswith("rate_"))
async def save_rate(callback: CallbackQuery):
    try:
        rating = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        db.add_feedback(user_id, rating)
        
        messages = {
            1: "😢 Спасибо за честность! Мы работаем над улучшением.",
            2: "😕 Спасибо! Расскажи, что нам улучшить?",
            3: "😐 Спасибо! Постараемся быть лучше.",
            4: "😊 Спасибо! Рады, что тебе понравилось!",
            5: "🌟 Спасибо! Рады, что ты доволен!"
        }
        
        await callback.message.edit_text(
            f"⭐ Спасибо за оценку {rating}!\n\n{messages.get(rating, '')}"
        )
        
        await bot.send_message(
            ADMIN_ID,
            f"📊 **Новая оценка поддержки**\n\n"
            f"👤 @{callback.from_user.username or callback.from_user.id}\n"
            f"⭐ Оценка: {rating}/5"
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await callback.answer()

# --- Статистика ---

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    stats = db.get_stats()
    
    today = datetime.now().strftime("%Y-%m-%d")
    db.cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE date(created_at) = ?",
        (today,)
    )
    today_tickets = db.cursor.fetchone()[0]
    
    db.cursor.execute(
        "SELECT problem, COUNT(*) FROM tickets GROUP BY problem ORDER BY COUNT(*) DESC LIMIT 5"
    )
    top_problems = db.cursor.fetchall()
    
    db.cursor.execute(
        "SELECT AVG(rating) FROM feedback"
    )
    avg_rating = db.cursor.fetchone()[0] or 0
    
    response = (
        f"💎 **Статистика бота**\n\n"
        f"📊 **Заявки:**\n"
        f"• Всего: {stats['total_tickets']}\n"
        f"• Открытых: {stats['open_tickets']}\n"
        f"• Закрытых: {stats['closed_tickets']}\n"
        f"• Сегодня: {today_tickets}\n\n"
        f"👤 **Пользователи:** {stats['total_users']}\n\n"
        f"⭐ **Средняя оценка:** {avg_rating:.1f}/5\n\n"
    )
    
    if top_problems:
        response += "📝 **Частые проблемы:**\n"
        for problem, count in top_problems:
            response += f"• {problem[:30]}... ({count})\n"
    
    await message.answer(response, parse_mode="Markdown")

# --- Админ-панель ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("🛡️ ⛔ Доступ запрещен")
        return
    
    tickets = db.get_tickets()
    if not tickets:
        await message.answer("💎 📭 Нет открытых заявок")
        return
    
    for ticket in tickets:
        await message.answer(
            f"🔥 **Заявка #{ticket[0]}**\n\n"
            f"👤 @{ticket[2] or ticket[1]}\n"
            f"🆔 ID: {ticket[1]}\n\n"
            f"📝 **Текст:**\n{ticket[3][:300]}\n\n"
            f"📅 {ticket[4]}\n\n"
            f"Чтобы ответить: /reply {ticket[0]} <текст>\n"
            f"Чтобы закрыть: /close {ticket[0]}",
            parse_mode="Markdown"
        )

# --- Остальные обработчики ---

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

# --- Запуск с веб-сервером ---

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
