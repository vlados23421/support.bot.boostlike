import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID
from database import Database
import aiohttp

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Состояния
class SupportState(StatesGroup):
    waiting_problem = State()

# Главное меню
def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Создать заявку", callback_data="ticket")],
            [InlineKeyboardButton(text="💱 Курс валют", callback_data="rate")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
            [InlineKeyboardButton(text="📊 Мой баланс", callback_data="balance")],
            [InlineKeyboardButton(text="👨‍💻 Связаться с оператором", callback_data="operator")]
        ]
    )

# FAQ
FAQ = {
    "Как пополнить баланс?": "💰 Пополнить можно через карту или криптовалюту",
    "Как создать задание?": "📝 Используй сайт или команду /newtask",
    "Почему не начисляются лайки?": "⏳ Подожди 5-30 минут",
    "Как вывести средства?": "💸 Вывод от 500 ₽ на карту"
}

# Старт
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот поддержки BoostSocialLikeBot\n\n"
        "Выбери действие:",
        reply_markup=main_menu()
    )

# Создание заявки
@dp.callback_query(F.data == "ticket")
async def create_ticket(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_problem)
    await callback.message.answer("✍️ Опиши свою проблему:")
    await callback.answer()

@dp.message(SupportState.waiting_problem)
async def save_ticket(message: types.Message, state: FSMContext):
    ticket_id = db.add_ticket(
        message.from_user.id,
        message.from_user.username or "без username",
        message.text
    )
    await message.answer(f"✅ Заявка #{ticket_id} создана!")
    await state.clear()
    
    await bot.send_message(
        ADMIN_ID,
        f"📩 Новая заявка #{ticket_id}\n"
        f"👤 @{message.from_user.username}\n"
        f"📝 {message.text[:200]}"
    )

# Курс валют
@dp.callback_query(F.data == "rate")
async def show_rate(callback: types.CallbackQuery):
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                usd_rub = round(data["rates"]["RUB"], 2)
                usd_byn = round(data["rates"]["BYN"], 2)
                eur_rub = round(data["rates"]["RUB"] / data["rates"]["EUR"], 2)
                
                await callback.message.answer(
                    f"💱 Курс валют:\n"
                    f"🇺🇸 USD/RUB: {usd_rub}\n"
                    f"🇪🇺 EUR/RUB: {eur_rub}\n"
                    f"🇺🇸 USD/BYN: {usd_byn}"
                )
    except:
        await callback.message.answer("⚠️ Не удалось получить курс")
    await callback.answer()

# FAQ
@dp.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=q, callback_data=f"faq_{i}")]
            for i, q in enumerate(FAQ.keys())
        ]
    )
    await callback.message.answer("❓ Частые вопросы:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("faq_"))
async def faq_answer(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1])
    question = list(FAQ.keys())[index]
    await callback.message.answer(f"❓ {question}\n\n{FAQ[question]}")
    await callback.answer()

# Баланс
@dp.callback_query(F.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    await callback.message.answer("💰 Твой баланс: 150 ₽")
    await callback.answer()

# Оператор
@dp.callback_query(F.data == "operator")
async def contact_operator(callback: types.CallbackQuery):
    await callback.message.answer("👨‍💻 Создай заявку, оператор ответит!")
    await callback.answer()

# Админ-панель
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    tickets = db.get_tickets()
    if not tickets:
        await message.answer("📭 Нет открытых заявок")
        return
    
    for ticket in tickets[:3]:
        await message.answer(
            f"📌 Заявка #{ticket[0]}\n"
            f"👤 @{ticket[2] or ticket[1]}\n"
            f"📝 {ticket[3][:100]}"
        )

@dp.message(Command("close"))
async def close_ticket(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        ticket_id = int(message.text.split()[1])
        db.close_ticket(ticket_id)
        await message.answer(f"✅ Заявка #{ticket_id} закрыта")
    except:
        await message.answer("❌ Использование: /close <id>")

# Запуск
async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
