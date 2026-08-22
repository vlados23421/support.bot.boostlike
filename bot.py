import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_TOKEN, ADMIN_ID
from database import Database
from emoji import Emoji
import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Состояния
class SupportState(StatesGroup):
    waiting_problem = State()

# --- Клавиатуры с Premium-эмодзи (ТОЛЬКО анимация) ---

def main_menu():
    """Главное меню — только анимированные эмодзи"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Создать заявку",  # ← БЕЗ эмодзи в тексте
                callback_data="ticket",
                icon_custom_emoji_id=Emoji.SHIELD  # ← только анимация
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
            )]
        ]
    )

def back_menu():
    """Кнопка назад"""
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
    """Меню FAQ"""
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
        "🚀 Связаться с оператором\n\n"
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

# --- Заявки ---

@dp.callback_query(F.data == "ticket")
async def create_ticket(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    msg = await callback.message.answer(
        "🛡️ **Опиши свою проблему подробно:**\n\n"
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
    
    await bot.send_message(
        ADMIN_ID,
        f"🔥 **Новая заявка #{ticket_id}**\n\n"
        f"👤 @{message.from_user.username or message.from_user.id}\n"
        f"🆔 ID: {message.from_user.id}\n\n"
        f"📝 **Текст:**\n{message.text[:500]}",
        parse_mode="Markdown"
    )

# --- Курс монет ---

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

# --- FAQ ---

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

# --- Оператор ---

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
    
    for ticket in tickets[:5]:
        await message.answer(
            f"🔥 **Заявка #{ticket[0]}**\n\n"
            f"👤 @{ticket[2] or ticket[1]}\n"
            f"🆔 ID: {ticket[1]}\n\n"
            f"📝 **Текст:**\n{ticket[3][:300]}\n\n"
            f"📅 {ticket[4]}",
            parse_mode="Markdown"
        )

@dp.message(Command("close"))
async def close_ticket(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        ticket_id = int(message.text.split()[1])
        db.close_ticket(ticket_id)
        await message.answer("🎉 ✅ Заявка #{ticket_id} закрыта")
    except:
        await message.answer("🛡️ ❌ Использование: /close <id>")

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    stats = db.get_stats()
    await message.answer(
        "💎 **Статистика:**\n\n"
        f"🛡️ Всего заявок: {stats['total_tickets']}\n"
        f"⭐ Открытых: {stats['open_tickets']}\n"
        f"🔥 Закрытых: {stats['closed_tickets']}\n"
        f"🎉 Пользователей: {stats['total_users']}",
        parse_mode="Markdown"
    )

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
