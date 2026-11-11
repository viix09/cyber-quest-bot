import asyncio
import logging
import os
import threading
from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН_ЕСЛИ_ТЕСТИРУЕШЬ_ЛОКАЛЬНО")

logging.basicConfig(level=logging.INFO)

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы не было ошибки портов) ---
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- КОД ТВОЕГО БОТА (без изменений) ---
class Quest(StatesGroup):
    m1_first = State()
    m1_second = State()
    m2 = State()
    m3 = State()
    m4a = State()
    m4b = State()
    m5 = State()
    final = State()

dp = Dispatcher()

async def add_letter(state: FSMContext, letter: str) -> str:
    data = await state.get_data()
    letters = data.get("letters", "") + letter
    await state.update_data(letters=letters)
    return " ".join(letters)

def kb(*rows: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=c) for t, c in row] for row in rows]
    )

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(letters="")
    await message.answer(
        "🕵️ <b>Кибердетективы: Дело о цифровом следе</b>\n\n"
        "В чате колледжа появился «Администратор» и украл аккаунты нескольких учащихся. "
        "Ты — юный кибердетектив. Пройди <b>5 миссий</b>, собери <b>5 букв</b> "
        "и составь код безопасности.\n\n"
        "Внимание: мошенники умеют маскироваться! 🚀\n\n"
        "<i>Чтобы начать заново — /start</i>",
        parse_mode="HTML",
    )
    await mission1_first(message, state)

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "🕵️ <b>Как играть</b>\n\n"
        "• Нажимай на кнопки под сообщением — это варианты ответа.\n"
        "• За каждый верный ответ получаешь <b>букву</b>.\n"
        "• Когда соберёшь все 5 — введи код одним сообщением.\n"
        "• Начать заново — /start",
        parse_mode="HTML",
    )

async def mission1_first(message: Message, state: FSMContext):
    await state.set_state(Quest.m1_first)
    await message.answer(
        "🔹 <b>Миссия 1. Фишинговая атака</b>\n\n"
        "Тебе пришли три сообщения:\n\n"
        "1️⃣ «Администрация колледжа: срочно подтвердите учётную запись по ссылке "
        "<code>college-belarus-login.xyz</code>, иначе доступ будет закрыт. Введите логин и пароль»\n\n"
        "2️⃣ «Преподаватель: завтра контрольная, повторите тему 5»\n\n"
        "3️⃣ «Привет, это мой новый аккаунт! Проголосуй за меня по ссылке и введи код из SMS»\n\n"
        "Найди <b>первое</b> мошенническое сообщение:",
        reply_markup=kb([("Сообщение 1", "m1_1")], [("Сообщение 2", "m1_2")], [("Сообщение 3", "m1_3")]),
        parse_mode="HTML",
    )

@dp.callback_query(Quest.m1_first, F.data.startswith("m1_"))
async def m1_first_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m1_1":
        await call.answer("✅ Верно")
        await call.message.edit_text(
            "✅ Верно! Подозрительный адрес <code>.xyz</code>, срочность и просьба ввести пароль — типичный фишинг.\n\n"
            "Но это не всё. В наборе есть <b>ещё одно</b> мошенническое сообщение. Какое?",
            reply_markup=kb([("Сообщение 2", "m1b_2")], [("Сообщение 3", "m1b_3")]),
            parse_mode="HTML",
        )
        await state.set_state(Quest.m1_second)
    else:
        await call.answer("❌ Не то. Ищи сообщение, где торопят и просят перейти по ссылке или ввести пароль.", show_alert=True)

@dp.callback_query(Quest.m1_second, F.data.startswith("m1b_"))
async def m1_second_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m1b_3":
        await call.answer("✅ Верно")
        letters = await add_letter(state, "К")
        await call.message.edit_text(
            "✅ Верно! Просьба ввести код из SMS — классика взлома аккаунтов.\n\n"
            f"🔍 Улика получена! Буква <b>К</b>.\nСобрано: <b>{letters}</b>",
            parse_mode="HTML",
        )
        await mission2(call.message, state)
    else:
        await call.answer("❌ Сообщение 2 — обычное. Ищи просьбу ввести код из SMS.", show_alert=True)

async def mission2(message: Message, state: FSMContext):
    await state.set_state(Quest.m2)
    await message.answer(
        "🔹 <b>Миссия 2. Цифровой след</b>\n\n"
        "Профиль учащегося открыт всем. Что из этого <b>опаснее всего</b> публиковать?",
        reply_markup=kb(
            [("Любимый предмет — информатика", "m2_subject")],
            [("Геолокация «жду у главного входа колледжа после занятий»", "m2_geo")],
            [("Имя питомца — Барсик", "m2_pet")],
            [("Любимая книга", "m2_book")],
        ),
        parse_mode="HTML",
    )

@dp.callback_query(Quest.m2, F.data.startswith("m2_"))
async def m2_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m2_geo":
        await call.answer("✅ Верно")
        letters = await add_letter(state, "И")
        await call.message.edit_text(
            "✅ Верно! Публичная геолокация + время = готовый маршрут для злоумышленника.\n\n"
            f"🔍 Буква <b>И</b>.\nСобрано: <b>{letters}</b>",
            parse_mode="HTML",
        )
        await mission3(call.message, state)
    else:
        await call.answer("❌ Это менее опасно. Подумай: что прямо указывает, где тебя найти в реальности?", show_alert=True)

async def mission3(message: Message, state: FSMContext):
    await state.set_state(Quest.m3)
    await message.answer(
        "🔹 <b>Миссия 3. Ловушка дроппера</b>\n\n"
        "Незнакомец пишет: «Привет! Просто получи посылку с банковской картой и передай курьеру. "
        "За это 50 BYN. Ничего незаконного, ты просто помощник».\n\n"
        "<b>Что делать?</b>",
        reply_markup=kb(
            [("А) Согласиться — лёгкие деньги", "m3_a")],
            [("Б) Отказаться и рассказать взрослым", "m3_b")],
            [("В) Спросить, можно ли больше", "m3_v")],
        ),
        parse_mode="HTML",
    )

@dp.callback_query(Quest.m3, F.data.startswith("m3_"))
async def m3_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m3_b":
        await call.answer("✅ Верно")
        letters = await add_letter(state, "Б")
        await call.message.edit_text(
            "✅ Верно! Так вербуют <b>дропперов</b> — людей, через которых «прогоняют» украденные деньги. "
            "Это не подработка, а риск стать соучастником преступления. Расскажи родителям или куратору.\n\n"
            f"🔍 Буква <b>Б</b>.\nСобрано: <b>{letters}</b>",
            parse_mode="HTML",
        )
        await mission4a(call.message, state)
    else:
        await call.answer("❌ Красный флаг: чужие карты и «лёгкие деньги». Правильный ответ — отказаться и рассказать взрослым.", show_alert=True)

async def mission4a(message: Message, state: FSMContext):
    await state.set_state(Quest.m4a)
    await message.answer(
        "🔹 <b>Миссия 4. Право и ответственность</b>\n\n"
        "Со скольки лет в Республике Беларусь может наступать уголовная ответственность "
        "за отдельные преступления, связанные с компьютерной информацией?",
        reply_markup=kb([("10 лет", "m4a_10")], [("14 лет", "m4a_14")], [("18 лет", "m4a_18")]),
        parse_mode="HTML",
    )

@dp.callback_query(Quest.m4a, F.data.startswith("m4a_"))
async def m4a_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m4a_14":
        await call.answer("✅ Верно")
        await call.message.edit_text(
            "✅ Верно! С 14 лет — но только за отдельные виды преступлений. "
            "По общему правилу ответственность наступает позже.\n\n"
            "Второй вопрос: «Взлом чужого аккаунта — это просто шутка?»",
            reply_markup=kb(
                [("Да, если ничего не украл", "m4b_yes")],
                [("Нет, это правонарушение или преступление", "m4b_no")],
            ),
            parse_mode="HTML",
        )
        await state.set_state(Quest.m4b)
    else:
        await call.answer("❌ Неверно. Верный ответ — 14 лет, но только за отдельные преступления.", show_alert=True)

@dp.callback_query(Quest.m4b, F.data.startswith("m4b_"))
async def m4b_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m4b_no":
        await call.answer("✅ Верно")
        letters = await add_letter(state, "Е")
        await call.message.edit_text(
            "✅ Верно! Закон не считает взлом безобидной шалостью.\n\n"
            f"🔍 Буква <b>Е</b>.\nСобрано: <b>{letters}</b>",
            parse_mode="HTML",
        )
        await mission5(call.message, state)
    else:
        await call.answer("❌ Взлом — это не шутка. Это правонарушение или преступление.", show_alert=True)

async def mission5(message: Message, state: FSMContext):
    await state.set_state(Quest.m5)
    await message.answer(
        "🔹 <b>Миссия 5. Защити аккаунт</b>\n\n"
        "Выбери самый надёжный пароль:",
        reply_markup=kb(
            [("qwerty123", "m5_1")],
            [("Маша2010", "m5_2")],
            [("7$kL!9pQ2#vM", "m5_3")],
            [("password", "m5_4")],
        ),
        parse_mode="HTML",
    )

@dp.callback_query(Quest.m5, F.data.startswith("m5_"))
async def m5_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "m5_3":
        await call.answer("✅ Верно")
        letters = await add_letter(state, "Р")
        await call.message.edit_text(
            "✅ Верно! Длинный, уникальный, с буквами разного регистра, цифрами и символами. "
            "И не забудь про двухфакторную аутентификацию.\n\n"
            f"🔍 Буква <b>Р</b>.\nСобрано: <b>{letters}</b>\n\n"
            "🏁 <b>Финал!</b> Введи собранный код безопасности (5 букв) одним сообщением:",
            parse_mode="HTML",
        )
        await state.set_state(Quest.final)
    else:
        await call.answer("❌ Такой пароль легко подобрать. Нужен длинный, уникальный и с символами.", show_alert=True)

@dp.message(Quest.final)
async def final_handler(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper().replace(" ", "")
    if code == "КИБЕР":
        await state.clear()
        await message.answer(
            "🎉 <b>Поздравляем, агент!</b>\n\n"
            "Ты собрал код <b>КИБЕР</b> и прошёл стажировку. Теперь ты настоящий кибердетектив!\n\n"
            "📋 <b>Памятка кибердетектива:</b>\n"
            "• Не переходи по подозрительным ссылкам\n"
            "• Никому не сообщай пароли и коды из SMS\n"
            "• Настрой приватность в соцсетях (убери геолокацию и лишние данные)\n"
            "• Не соглашайся получать/передавать чужие карты и деньги\n"
            "• Если что-то пошло не так — расскажи родителям, куратору и звони <b>102</b>\n\n"
            "Молодец! 🕵️‍♂️\n<i>Пройти заново — /start</i>",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "❌ Неверный код.\n"
            "Помни: буквы выдаются за верные ответы в миссиях — их должно быть 5, "
            "и вместе они складываются в слово. Попробуй ещё раз:"
        )

@dp.message()
async def fallback(message: Message, state: FSMContext):
    await message.answer("👉 Используй кнопки под сообщением, чтобы выбрать ответ.")

# --- ЗАПУСК ВСЕГО ВМЕСТЕ ---
async def main():
    # Запускаем Flask в отдельном потоке, чтобы он не мешал боту
    threading.Thread(target=run_flask, daemon=True).start()
    
    bot = Bot(token=BOT_TOKEN)
    print("Бот запущен и готов к работе на Render!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())