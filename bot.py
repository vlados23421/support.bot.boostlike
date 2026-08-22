import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID
from database import db
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Состояния ---
class SupportState(StatesGroup):
    waiting_problem = State()
    waiting_reply = State()

# --- Клавиатуры ---
def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Создать заявку", callback_data="ticket")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
            [InlineKeyboardButton(text="💱 Курс валют", callback_data="rate")],
            [InlineKeyboardButton(text="📊 Мой баланс", callback_data="balance")],
            [InlineKeyboardButton(text="👨‍💻 Связаться с оператором", callback_data="operator")]
        ]
    )

# --- FAQ ---
FAQ = {
    "Как пополнить баланс?": "💰 Пополнить баланс можно через банковскую карту или криптовалюту. Минимальная сумма 100 ₽.",
    "Как создать задание?": "📝 Используй команду /newtask или наш сайт. Укажи ссылку на пост и количество лайков.",
    "Почему не начисляются лайки?": "⏳ Лайки начисляются в течение 5-30 минут. Если прошло больше часа — создай заявку.",
    "Как вывести средства?": "💸 Вывод от 500 ₽ на карту. Команда /withdraw или в личном кабинете."
}

# --- Обработчик команд ---

@dp.message(Command("start"))
async def start_command(message: types.Message):
    # Регистрируем пользователя
    db.add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    await message.answer(
        "👋 Привет! Я бот поддержки BoostSocialLikeBot\n\n"
        "Выбери нужное действие:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "ticket")
async def create_ticket(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_problem)
    await callback.message.answer("✍️ Опиши свою проблему подробно (укажи ID заказа, если есть):")
    await callback.answer()

@dp.message(SupportState.waiting_problem)
async def save_ticket(message: types.Message, state: FSMContext):
    ticket_id = db.add_ticket(
        message.from_user.id,
        message.from_user.username or "без username",
        message.text
    )
    
    await message.answer(
        f"✅ Заявка #{ticket_id} создана!\n"
        "Оператор свяжется с тобой в ближайшее время."
    )
    await state.clear()
    
    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"📩 **Новая заявка #{ticket_id}**\n"
        f"👤 @{message.from_user.username or message.from_user.id}\n"
        f"📝 {message.text[:200]}...",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=q, callback_data=f"faq_{i}")] 
            for i, q in enumerate(FAQ.keys())
        ]
    )
    await callback.message.answer("❓ **Часто задаваемые вопросы:**", 
                                  reply_markup=keyboard,
                                  parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("faq_"))
async def faq_answer(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1])
    question = list(FAQ.keys())[index]
    answer = FAQ[question]
    await callback.message.answer(f"❓ {question}\n\n{answer}")
    await callback.answer()

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
                    "💱 **Курсы валют**\n\n"
                    f"🇺🇸 USD/RUB: {usd_rub}\n"
                    f"🇪🇺 EUR/RUB: {eur_rub}\n"
                    f"🇺🇸 USD/BYN: {usd_byn}",
                    parse_mode="Markdown"
                )
    except:
        await callback.message.answer("⚠️ Не удалось получить курс. Попробуйте позже.")
    await callback.answer()

@dp.callback_query(F.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    await callback.message.answer(
        "💰 **Твой баланс**\n\n"
        "Баланс: 150 ₽\n"
        "Доступно к выводу: 150 ₽\n\n"
        "Для пополнения: /deposit"
    )
    await callback.answer()

@dp.callback_query(F.data == "operator")
async def contact_operator(callback: types.CallbackQuery):
    await callback.message.answer(
        "👨‍💻 **Связь с оператором**\n\n"
        "Создай заявку через кнопку «Создать заявку».\n"
        "Оператор ответит в ближайшее время!"
    )
    await callback.answer()

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    tickets = db.get_tickets("open")
    if not tickets:
        await message.answer("📭 Нет открытых заявок")
        return
    
    for ticket in tickets[:3]:
        await message.answer(
            f"📌 **Заявка #{ticket[0]}**\n"
            f"👤 @{ticket[2] or ticket[1]}\n"
            f"📝 {ticket[3][:200]}\n"
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
        await message.answer(f"✅ Заявка #{ticket_id} закрыта")
    except:
        await message.answer("❌ Использование: /close <id>")

@dp.message()
async def handle_other(message: types.Message):
    await message.answer(
        "❓ Я не понял команду.\n"
        "Нажми /start для главного меню."
    )

# --- Запуск ---
async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
