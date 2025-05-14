import asyncio
import json
import os
import random
from datetime import datetime, time, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Загрузка токена из
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env !")

# Создание бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Загрузка программы тренировок
with open("program.json", "r", encoding="utf-8") as f:
    PROGRAM = json.load(f)

# Прогресс
PROGRESS_FILE = "progress.json"
WEIGHT_FILE = "weight.json"

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USER_PROGRESS = load_json(PROGRESS_FILE)
USER_WEIGHT = load_json(WEIGHT_FILE)

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📆 Моя тренировка")],
        [KeyboardButton(text="📈 Прогресс")],
        [KeyboardButton(text="🎯 Выбери цель")],
        [KeyboardButton(text="🍏 Мой рацион")],
        [KeyboardButton(text="⚖️ Мой вес")],
        [KeyboardButton(text="💧 Пить воду")],
        [KeyboardButton(text="🏠 Главное меню")],
    ],
    resize_keyboard=True,
)

goal_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=goal)] for goal in ["Похудение", "Сила", "Общая форма"]] +
             [[KeyboardButton(text="🏠 Главное меню")]],
    resize_keyboard=True,
)

diet_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
    resize_keyboard=True,
)

goals = {
    "Похудение": ["Кардио тренировка", "Скакалка", "Бег"],
    "Сила": ["Приседания с весом", "Отжимания с утяжелениями", "Тяга на спину"],
    "Общая форма": ["Приседания", "Отжимания", "Планка"]
}

tips = [
    "Не забывай про растяжку после тренировки! 🧘‍♂️",
    "Пей воду, котик! 💧",
    "Слушай своё тело — отдых тоже важен! 💤",
    "Не бросай тренировку на половине пути! 💪"
]

user_water_intake = {}
user_input_mode = {}

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, я Фитнес Котик, помогу тебе с тренировками и отслеживанием прогресса.\n\n"
        "Нажми на кнопку ниже, чтобы начать!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Старт")]],
            resize_keyboard=True
        )
    )

# Кнопка "Старт"
@dp.message(lambda msg: msg.text == "Старт")
async def start_button(message: types.Message):
    await message.answer("Ты выбрал старт! Чем могу помочь?", reply_markup=main_kb)

# Моя тренировка
@dp.message(lambda msg: msg.text == "📆 Моя тренировка")
async def send_training(message: types.Message):
    user_id = str(message.from_user.id)
    day = USER_PROGRESS.get(user_id, 0)

    if day >= len(PROGRAM):
        await message.answer("Ты прошёл всю программу! 🔥")
        return

    workout = PROGRAM[day]
    motivation = random.choice(tips)

    USER_PROGRESS[user_id] = day + 1
    save_json(PROGRESS_FILE, USER_PROGRESS)

    await message.answer(f"<b>День {day + 1} из 30</b>\n\n{workout}\n\n{motivation}", reply_markup=main_kb)

# Прогресс
@dp.message(lambda msg: msg.text == "📈 Прогресс")
async def show_progress(message: types.Message):
    user_id = str(message.from_user.id)
    day = USER_PROGRESS.get(user_id, 0)

    if day >= len(PROGRAM):
        progress_text = "Ты завершил(а) всю программу тренировок! 💪"
    else:
        progress_text = f"Ты на <b>{day + 1}-м дне</b> из 30. Продолжай в том же духе! 🔥"

    await message.answer(progress_text, reply_markup=main_kb)

# Пить воду
@dp.message(lambda msg: msg.text == "💧 Пить воду")
async def water_intake(message: types.Message):
    user_id = str(message.from_user.id)
    user_input_mode[user_id] = "water"
    await message.answer("Сколько воды ты выпил(а) сегодня? Напиши в литрах (например, 1.5).")

# Мой вес
@dp.message(lambda msg: msg.text == "⚖️ Мой вес")
async def ask_weight(message: types.Message):
    user_id = str(message.from_user.id)
    user_input_mode[user_id] = "weight"
    await message.answer("Напиши свой текущий вес в килограммах (например, 72.5):")

# Обработка числового ввода
@dp.message(lambda msg: msg.text.replace('.', '', 1).isdigit())
async def handle_input(message: types.Message):
    user_id = str(message.from_user.id)
    mode = user_input_mode.get(user_id)

    if mode == "water":
        water_amount = float(message.text)
        user_water_intake[user_id] = user_water_intake.get(user_id, 0) + water_amount
        await message.answer(f"Ты выпил(а) {water_amount} литра воды! Всего сегодня: {user_water_intake[user_id]} л 💧")

    elif mode == "weight":
        new_weight = float(message.text)
        previous = USER_WEIGHT.get(user_id)
        diff = ""

        if previous is not None:
            change = new_weight - previous
            if change > 0:
                diff = f" (+{change:.1f} кг)"
            elif change < 0:
                diff = f" ({change:.1f} кг)"
            else:
                diff = " (без изменений)"

        USER_WEIGHT[user_id] = new_weight
        save_json(WEIGHT_FILE, USER_WEIGHT)
        await message.answer(f"Вес сохранён: {new_weight} кг{diff}")

    else:
        await message.answer("Пожалуйста, сначала выбери функцию (вода или вес).")

# Выбор цели
@dp.message(lambda msg: msg.text == "🎯 Выбери цель")
async def select_goal(message: types.Message):
    await message.answer("Выбери свою цель:", reply_markup=goal_kb)

@dp.message(lambda msg: msg.text in goals.keys())
async def goal_selected(message: types.Message):
    goal = message.text
    program = goals.get(goal, [])
    goal_text = "\n".join(program)

    await message.answer(f"Ты выбрал(а) цель: {goal}. Твоя программа:\n{goal_text}", reply_markup=main_kb)

# Мой рацион
@dp.message(lambda msg: msg.text == "🍏 Мой рацион")
async def my_diet(message: types.Message):
    await message.answer(
        "Вот несколько рекомендаций для твоего рациона питания:\n\n"
        "1. Белки: курица, рыба, яйца, бобовые.\n"
        "2. Углеводы: картофель, рис, овсянка.\n"
        "3. Жиры: авокадо, оливковое масло, орехи.\n\n"
        "Не забывай пить воду и соблюдать баланс макроэлементов!",
        reply_markup=diet_kb
    )

# Главное меню
@dp.message(lambda msg: msg.text == "🏠 Главное меню")
async def back_to_main_menu(message: types.Message):
    await message.answer("Ты вернулся в главное меню. Чем могу помочь?", reply_markup=main_kb)

# Напоминание о воде
async def water_reminder():
    while True:
        now = datetime.now()
        target_time = datetime.combine(now.date(), time(hour=10))
        if now > target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        for user_id in user_water_intake:
            try:
                await bot.send_message(user_id, "🐾 Не забывай пить воду! 💧")
            except Exception as e:
                print(f"Ошибка при отправке уведомления {user_id}: {e}")

# Запуск бота
async def main():
    asyncio.create_task(water_reminder())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
