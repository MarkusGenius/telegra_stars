from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import asyncio

API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_ID = 123456789  # твой Telegram ID
SBP_PHONE = "+7 999 123 45 67"  # номер для СБП

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

class OrderForm(StatesGroup):
    waiting_for_stars = State()
    waiting_for_username = State()
    waiting_for_receipt = State()

@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я помогу тебе купить звёзды ⭐\n\n"
        "Напиши, сколько звёзд хочешь (минимум 50):"
    )
    await OrderForm.waiting_for_stars.set()

@dp.message_handler(state=OrderForm.waiting_for_stars)
async def process_stars(message: types.Message, state: FSMContext):
    try:
        stars = int(message.text)
        if stars < 50:
            await message.answer("⚠️ Минимум 50 звёзд! Попробуй ещё раз ✨")
            return
        await state.update_data(stars=stars)
        await message.answer("Отлично! ⭐ Теперь укажи свой <b>@username</b> 👤")
        await OrderForm.waiting_for_username.set()
    except:
        await message.answer("❌ Нужно ввести число. Попробуй ещё раз!")

@dp.message_handler(state=OrderForm.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text
    data = await state.get_data()
    stars = data["stars"]

    await state.update_data(username=username)

    await message.answer(
        f"✨ Отлично! Вот твой заказ:\n\n"
        f"⭐ Количество звёзд: <b>{stars}</b>\n"
        f"👤 Пользователь: <b>{username}</b>\n\n"
        f"💳 Оплата через СБП:\n"
        f"📱 Телефон: <b>{SBP_PHONE}</b>\n"
        f"🏦 Банк: любой\n\n"
        "После перевода загрузи сюда скрин/чек 📸"
    )
    await OrderForm.waiting_for_receipt.set()

@dp.message_handler(content_types=["photo"], state=OrderForm.waiting_for_receipt)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    stars = data["stars"]
    username = data["username"]

    # Отправляем админу скрин и детали заказа
    photo_id = message.photo[-1].file_id
    await bot.send_photo(
        ADMIN_ID,
        photo=photo_id,
        caption=f"🔔 Новый заказ!\n\n"
                f"⭐ Количество: {stars}\n"
                f"👤 Пользователь: {username}\n\n"
                "📸 Чек выше"
    )

    # Кнопки подтверждения
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Звёзды пришли", callback_data="stars_ok"),
        InlineKeyboardButton("❌ Звёзды не пришли", callback_data="stars_fail")
    )

    await message.answer("Спасибо! 🔎 Мы проверим оплату. Жди свои звёзды ✨", reply_markup=keyboard)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data in ["stars_ok", "stars_fail"])
async def process_callback(callback: types.CallbackQuery):
    if callback.data == "stars_ok":
        await callback.message.edit_text("🎉 Отлично! Звёзды уже у тебя ✨ Спасибо за покупку 💜")
    else:
        await callback.message.edit_text("😔 Понял тебя. Мы проверим и поможем как можно скорее 🛠")
