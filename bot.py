import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
import json
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_FIRST_NAME = 1
WAITING_FOR_SURNAME = 2
ADMIN_SELECT_USER = 1
ADMIN_ADD_POINTS = 2
ADMIN_CREATE_TASK = 1
ADMIN_SET_TASK_POINTS = 2
USER_SELECT_TASK = 100
USER_SEND_TASK_CONTENT = 101
USER_SUBMIT_TASK = 102
ADMIN_FIX_ID_SELECT_USER = 1
ADMIN_FIX_ID_SET_NEW = 2
ADMIN_REVIEW_SELECT = 1
ADMIN_CREATE_PRODUCT_NAME = 3
ADMIN_CREATE_PRODUCT_DESCRIPTION = 4
ADMIN_CREATE_PRODUCT_PRICE = 5
USER_BUY_PRODUCT = 1
USER_CONFIRM_PURCHASE = 2
ADMIN_CONFIRM_RESET = 1
ADMIN_DELETE_PRODUCT = 6
ADMIN_SET_PRODUCT_QUANTITY = 7
ADMIN_CREATE_TASK_TITLE = 8
ADMIN_CREATE_TASK_TYPE = 9
USER_SEND_MORE_FILES = 103

# Файлы для хранения данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'users_data.json')
TASKS_FILE = os.path.join(BASE_DIR, 'tasks_data.json')
SUBMISSIONS_FILE = os.path.join(BASE_DIR, 'submissions_data.json')
PRODUCTS_FILE = os.path.join(BASE_DIR, 'products_data.json')
ORDERS_FILE = os.path.join(BASE_DIR, 'orders_data.json')

# ID администратора (замените на ваши Telegram ID)
ADMIN_IDS = [424081501, 421897893]  # Два администратора

def initialize_files():
    """Создание файлов если их нет"""
    files = [DATA_FILE, TASKS_FILE, PRODUCTS_FILE, SUBMISSIONS_FILE, ORDERS_FILE]
    for file in files:
        if not os.path.exists(file):
            save_data({}, file)
            logger.info(f"Создан файл: {file}")

def load_products():
    return load_data(PRODUCTS_FILE)

def save_products(products):
    save_data(products, PRODUCTS_FILE)

def load_orders():
    return load_data(ORDERS_FILE)

def save_orders(orders):
    save_data(orders, ORDERS_FILE)

def generate_product_id(products):
    """Генерация уникального ID для товара"""
    if not products:
        return 1

    # Находим максимальный ID среди ключей
    max_id = 0
    for product_id in products.keys():
        try:
            num_id = int(product_id)
            if num_id > max_id:
                max_id = num_id
        except ValueError:
            continue

    return max_id + 1

def generate_task_id(tasks):
    """Генерация уникального ID для задания"""
    if not tasks:
        return 1
    max_id = 0
    for task_id in tasks.keys():
        try:
            num_id = int(task_id)
            if num_id > max_id:
                max_id = num_id
        except ValueError:
            continue
    return max_id + 1
    
def load_data(filename):
    """Загрузка данных из файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        return {}
    except Exception as e:
        logger.error(f"Ошибка загрузки данных из {filename}: {e}")
        return {}

def save_data(data, filename):
    """Сохранение данных в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Данные успешно сохранены в {filename}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения данных в {filename}: {e}")

def load_users():
    return load_data(DATA_FILE)

def save_users(users):
    save_data(users, DATA_FILE)

def load_tasks():
    return load_data(TASKS_FILE)

def save_tasks(tasks):
    save_data(tasks, TASKS_FILE)

def load_submissions():
    return load_data(SUBMISSIONS_FILE)

def save_submissions(submissions):
    save_data(submissions, SUBMISSIONS_FILE)

def get_main_keyboard(user_id=None):
    """Главная клавиатура с кнопками"""
    keyboard = [
        [KeyboardButton("👤 Профиль"), KeyboardButton("🛍️ Магазин")],
        [KeyboardButton("📊 Рейтинг участников"), KeyboardButton("📤 Отправить задание")]
    ]

    # Добавляем кнопку администратора если пользователь - админ
    if user_id and is_admin(user_id):
        keyboard.append([KeyboardButton("👨‍💼 Панель администратора")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        [KeyboardButton("👥 Список пользователей"), KeyboardButton("⭐ Добавить баллы")],
        [KeyboardButton("📝 Создать задание"), KeyboardButton("📋 Список заданий")],
        [KeyboardButton("📨 Проверка заданий"), KeyboardButton("🛍️ Добавить товар")],
        [KeyboardButton("📦 Список товаров"), KeyboardButton("🗑️ Удалить товар")],
        [KeyboardButton("🆔 Исправить ID"), KeyboardButton("🗑️ Сбросить пользователей")],
        [KeyboardButton("🗑️ Удалить задание"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def generate_unique_id(items):
    """Генерация уникального ID"""
    if not items:
        return 1

    # Собираем все существующие ID
    existing_ids = []
    for user_data in items.values():
        if 'unique_id' in user_data:
            existing_ids.append(user_data['unique_id'])

    # Если нет ID, начинаем с 1
    if not existing_ids:
        return 1

    # Находим максимальный ID и возвращаем следующий
    return max(existing_ids) + 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    users = load_users()

    if str(user_id) in users:
        user_data = users[str(user_id)]
        await update.message.reply_text(
            f"✅ Вы уже зарегистрированы!\n\n"
            f"👤 Имя: {user_data['first_name']} {user_data['surname']}\n"
            f"🆔 Ваш ID: #{user_data['unique_id']}\n\n"
            f"Используйте кнопки ниже для работы с ботом.",
            reply_markup=get_main_keyboard(user_id)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "👋 Добро пожаловать!\n\n"
            "Для начала работы необходимо зарегистрироваться.\n\n"
            "📝 Пожалуйста, введите ваше имя:"
        )
        return WAITING_FOR_FIRST_NAME

async def register_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода имени при регистрации"""
    first_name = update.message.text.strip()

    if not first_name or len(first_name) < 2:
        await update.message.reply_text(
            "❌ Имя должно содержать минимум 2 символа. Попробуйте еще раз:"
        )
        return WAITING_FOR_FIRST_NAME

    if len(first_name) > 50:
        await update.message.reply_text(
            "❌ Имя слишком длинное. Максимум 50 символов. Попробуйте еще раз:"
        )
        return WAITING_FOR_FIRST_NAME

    # Сохраняем имя в контексте
    context.user_data['first_name'] = first_name

    await update.message.reply_text(
        f"✅ Имя сохранено: {first_name}\n\n"
        "Теперь введите вашу фамилию:"
    )
    return WAITING_FOR_SURNAME

async def register_surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода фамилии при регистрации"""
    surname = update.message.text.strip()

    if not surname or len(surname) < 2:
        await update.message.reply_text(
            "❌ Фамилия должна содержать минимум 2 символа. Попробуйте еще раз:"
        )
        return WAITING_FOR_SURNAME

    if len(surname) > 50:
        await update.message.reply_text(
            "❌ Фамилия слишком длинная. Максимум 50 символов. Попробуйте еще раз:"
        )
        return WAITING_FOR_SURNAME

    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id in users:
        await update.message.reply_text(
            "⚠️ Вы уже зарегистрированы!",
            reply_markup=get_main_keyboard(int(user_id))
        )
        return ConversationHandler.END

    # Получаем имя из контекста
    first_name = context.user_data.get('first_name')
    
    # Генерируем уникальный ID
    unique_id = generate_unique_id(users)

    users[user_id] = {
    'first_name': first_name,
    'surname': surname,
    'name': f"{first_name} {surname}",
    'unique_id': unique_id,
    'points': 0,           # Текущие баллы (списываются при покупках)
    'total_earned': 0,     # Всего заработано (не списывается, только начисляется)
    'registered_at': update.message.date.isoformat()
}
    save_users(users)

    logger.info(f"Зарегистрирован новый пользователь: {first_name} {surname} (ID: {unique_id})")

    await update.message.reply_text(
        f"✅ Регистрация успешно завершена!\n\n"
        f"📝 Ваше имя: {first_name}\n"
        f"📝 Ваша фамилия: {surname}\n"
        f"🆔 Ваш уникальный ID: #{unique_id}\n"
        f"⭐ Начальные баллы: 0\n\n"
        f"Теперь вы можете пользоваться всеми функциями бота!",
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

    # Очищаем контекст
    context.user_data.pop('first_name', None)
    
    return ConversationHandler.END

async def show_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать рейтинг участников"""
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы. Используйте команду /start для регистрации."
        )
        return

    if not users:
        await update.message.reply_text(
            "📊 <b>Рейтинг участников</b>\n\n"
            "Пока нет зарегистрированных участников.",
            parse_mode='HTML',
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return

    # Сортируем пользователей по total_earned (всего заработано)
    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1]['total_earned'],  # Изменено с 'points' на 'total_earned'
        reverse=True
    )

    rating_text = "📊 <b>Рейтинг участников (общий заработок)</b>\n\n"

    for index, (user_telegram_id, user_data) in enumerate(sorted_users, 1):
        medal = ""
        if index == 1:
            medal = "🥇 "
        elif index == 2:
            medal = "🥈 "
        elif index == 3:
            medal = "🥉 "

        user_name = f"{user_data['first_name']} {user_data['surname']}"

        rating_text += (
            f"{medal}<b>{index}.</b> {user_name} - {user_data['total_earned']} баллов\n"
        )

        if index % 5 == 0 and index < len(sorted_users):
            rating_text += "────────────────────\n"

    # Добавляем статистику
    total_users = len(users)
    # Считаем по total_earned
    total_points = sum(user['total_earned'] for user in users.values())
    average_points = total_points / total_users if total_users > 0 else 0

    rating_text += f"\n📈 <b>Статистика:</b>\n"
    rating_text += f"👥 Всего участников: {total_users}\n"
    rating_text += f"⭐ Всего заработано: {total_points}\n"
    rating_text += f"📊 Средний заработок: {average_points:.1f}"

    await update.message.reply_text(
        rating_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы. Используйте команду /start для регистрации."
        )
        return

    user_data = users[user_id]

    profile_text = (
        "👤 <b>Ваш профиль</b>\n\n"
        f"📝 Имя: {user_data['first_name']}\n"
        f"📝 Фамилия: {user_data['surname']}\n"
        f"🆔 Уникальный ID: #{user_data['unique_id']}\n"
        f"💰 Текущие баллы: {user_data['points']}\n"
        f"⭐ Всего заработано: {user_data['total_earned']}\n"
        f"📅 Зарегистрирован: {user_data.get('registered_at', 'Неизвестно')}"
    )

    await update.message.reply_text(
        profile_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard(update.effective_user.id)
    )
    
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать магазин товаров"""
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы. Используйте команду /start для регистрации."
        )
        return ConversationHandler.END

    products = load_products()
    user_data = users[user_id]

    if not products:
        await update.message.reply_text(
            "🛍️ <b>Магазин</b>\n\n"
            "На данный момент товаров в магазине нет.\n"
            "Ожидайте новых поступлений!",
            parse_mode='HTML',
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    shop_text = f"🛍️ <b>Магазин товаров</b>\n\n💳 <b>Ваш баланс:</b> {user_data['points']} баллов\n\n"

    for product_id, product in products.items():
        quantity_text = "∞" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."
        available = product.get('quantity', 0) == 0 or product.get('quantity', 0) > product.get('sold', 0)

        status_icon = "✅" if available else "❌"
        status_text = "Доступен" if available else "Нет в наличии"

        shop_text += (
            f"{status_icon} <b>Товар #{product_id}</b> - {status_text}\n"
            f"📦 {product['name']}\n"
            f"📝 {product['description']}\n"
            f"💰 Цена: {product['price']} баллов\n"
            f"📦 В наличии: {quantity_text}\n"
            f"────────────────────\n"
        )

    shop_text += "\nЧтобы купить товар, нажмите на кнопку с номером товара:"

    # Создаем клавиатуру с товарами
    keyboard = []
    for product_id, product in products.items():
        available = product.get('quantity', 0) == 0 or product.get('quantity', 0) > product.get('sold', 0)
        if available:
            keyboard.append([KeyboardButton(f"🛒 Купить товар #{product_id}")])

    if not keyboard:
        shop_text = "🛍️ <b>Магазин</b>\n\n❌ На данный момент все товары распроданы."
        await update.message.reply_text(
            shop_text,
            parse_mode='HTML',
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    keyboard.append([KeyboardButton("🔙 Назад")])

    await update.message.reply_text(
        shop_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return USER_BUY_PRODUCT

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора товара для покупки"""
    text = update.message.text

    if text == "🔙 Назад":
        await update.message.reply_text(
            "🔙 Возврат в главное меню.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    # Извлекаем ID товара из текста
    try:
        product_id = text.split('#')[1].split(' ')[0]
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора товара. Попробуйте еще раз:",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return USER_BUY_PRODUCT

    user_id = str(update.effective_user.id)
    users = load_users()
    products = load_products()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    if product_id not in products:
        await update.message.reply_text(
            "❌ Товар не найден.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    user_data = users[user_id]
    product = products[product_id]

    # Проверяем доступность товара
    available = product.get('quantity', 0) == 0 or product.get('quantity', 0) > product.get('sold', 0)
    if not available:
        await update.message.reply_text(
            "❌ Этот товар закончился.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    # Сохраняем выбранный товар в контексте
    context.user_data['selected_product'] = product
    context.user_data['selected_product_id'] = product_id

    # Показываем подтверждение покупки
    quantity_text = "без ограничений" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."
    remaining = product.get('quantity', 0) - product.get('sold', 0) if product.get('quantity', 0) > 0 else "∞"

    confirmation_text = (
        f"🛒 <b>Подтверждение покупки</b>\n\n"
        f"🎁 <b>Товар:</b> {product['name']}\n"
        f"📝 <b>Описание:</b> {product['description']}\n"
        f"💰 <b>Цена:</b> {product['price']} баллов\n"
        f"📦 <b>В наличии:</b> {quantity_text}\n"
        f"🔢 <b>Осталось:</b> {remaining} шт.\n\n"
        f"💳 <b>Ваш баланс:</b> {user_data['points']} баллов\n"
        f"🔮 <b>Останется после покупки:</b> {user_data['points'] - product['price']} баллов\n\n"
        f"<b>Вы уверены, что хотите купить этот товар?</b>"
    )

    # Создаем клавиатуру для подтверждения
    keyboard = [
        [KeyboardButton("✅ Да, купить товар"), KeyboardButton("❌ Нет, отменить")],
        [KeyboardButton("🔙 Назад к товарам")]
    ]

    await update.message.reply_text(
        confirmation_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return USER_CONFIRM_PURCHASE

async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения покупки"""
    text = update.message.text

    if text == "🔙 Назад к товарам":
        return await shop(update, context)

    if text in ["❌ Нет, отменить", "🔙 Назад"]:
        await update.message.reply_text(
            "❌ Покупка отменена.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    if text != "✅ Да, купить товар":
        await update.message.reply_text(
            "❌ Неизвестная команда. Пожалуйста, используйте кнопки для подтверждения.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return USER_CONFIRM_PURCHASE

    # Получаем сохраненный товар из контекста
    product = context.user_data.get('selected_product')
    product_id = context.user_data.get('selected_product_id')

    if not product or not product_id:
        await update.message.reply_text(
            "❌ Ошибка: товар не найден.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    user_id = str(update.effective_user.id)
    users = load_users()
    products = load_products()

    # Обновляем данные товара (на случай изменений)
    if product_id not in products:
        await update.message.reply_text(
            "❌ Товар больше не доступен.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    product = products[product_id]
    user_data = users[user_id]

    # Проверяем доступность товара еще раз
    available = product.get('quantity', 0) == 0 or product.get('quantity', 0) > product.get('sold', 0)
    if not available:
        await update.message.reply_text(
            "❌ Этот товар закончился.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    # Проверяем достаточно ли баллов
    if user_data['points'] < product['price']:
        await update.message.reply_text(
            f"❌ <b>Недостаточно баллов!</b>\n\n"
            f"💰 Стоимость товара: {product['price']} баллов\n"
            f"💳 Ваш баланс: {user_data['points']} баллов\n"
            f"🔻 Не хватает: {product['price'] - user_data['points']} баллов\n\n"
            f"Пополните баланс и попробуйте снова!",
            parse_mode='HTML',
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    # Списываем баллы из текущих (points), но total_earned остается неизменным
    users[user_id]['points'] -= product['price']
    save_users(users)

    # Обновляем количество товара
    if product.get('quantity', 0) > 0:
        products[product_id]['sold'] = products[product_id].get('sold', 0) + 1
    save_products(products)

    # Создаем заказ
    orders = load_orders()
    order_id = generate_unique_id(orders)

    orders[order_id] = {
        'user_id': user_id,
        'user_name': f"{user_data['first_name']} {user_data['surname']}",
        'user_unique_id': user_data['unique_id'],
        'product_id': product_id,
        'product_name': product['name'],
        'product_description': product['description'],
        'price': product['price'],
        'order_time': datetime.now().isoformat(),
        'status': 'completed'
    }
    save_orders(orders)

    # Уведомляем администраторов
    for admin_id in ADMIN_IDS:
        try:
            remaining = "∞" if product.get('quantity', 0) == 0 else product.get('quantity', 0) - products[product_id]['sold']
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🛒 <b>Новая покупка!</b>\n\n"
                     f"👤 <b>Покупатель:</b> {user_data['first_name']} {user_data['surname']} (ID: #{user_data['unique_id']})\n"
                     f"🎁 <b>Товар:</b> {product['name']}\n"
                     f"💰 <b>Цена:</b> {product['price']} баллов\n"
                     f"📦 <b>Осталось:</b> {remaining} шт.\n"
                     f"🆔 <b>Заказ #:</b> {order_id}\n"
                     f"🕒 <b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    remaining_text = "∞" if product.get('quantity', 0) == 0 else product.get('quantity', 0) - products[product_id]['sold']

    await update.message.reply_text(
        f"🎉 <b>Поздравляем с покупкой!</b>\n\n"
        f"🎁 <b>Товар:</b> {product['name']}\n"
        f"📝 <b>Описание:</b> {product['description']}\n"
        f"💰 <b>Списано:</b> {product['price']} баллов\n"
        f"💳 <b>Остаток на балансе:</b> {users[user_id]['points']} баллов\n"
        f"📦 <b>Осталось товара:</b> {remaining_text} шт.\n"
        f"🆔 <b>Номер заказа:</b> #{order_id}\n\n"
        f"Спасибо за покупку! 🎊",
        parse_mode='HTML',
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

    # Очищаем контекст
    context.user_data.pop('selected_product', None)
    context.user_data.pop('selected_product_id', None)

    return ConversationHandler.END
    
async def admin_create_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания товара"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    # Очищаем контекст
    context.user_data.pop('product_name', None)
    context.user_data.pop('product_description', None)

    await update.message.reply_text(
        "🛍️ <b>Добавление нового товара</b>\n\n"
        "Введите название товара:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_CREATE_PRODUCT_NAME

async def admin_delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список заданий для удаления с inline-кнопками"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    tasks = load_tasks()
    if not tasks:
        await update.message.reply_text(
            "📭 Нет заданий для удаления.",
            reply_markup=get_admin_keyboard()
        )
        return

    keyboard = []
    for task_id, task in tasks.items():
        # Обрезаем описание до 20 символов
        desc_preview = (task['description'][:20] + '...') if len(task['description']) > 20 else task['description']
        button_text = f"#{task_id} - {desc_preview}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"del_task_{task_id}")])

    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_task")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🗑️ <b>Выберите задание для удаления:</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    
async def admin_create_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия товара"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление товара отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем название товара
    context.user_data['product_name'] = text

    await update.message.reply_text(
        f"📦 <b>Название товара:</b> {text}\n\n"
        "Теперь введите описание товара:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_CREATE_PRODUCT_DESCRIPTION

async def admin_create_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания товара"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление товара отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем описание товара
    context.user_data['product_description'] = text

    await update.message.reply_text(
        f"📦 <b>Название товара:</b> {context.user_data['product_name']}\n"
        f"📝 <b>Описание:</b> {text}\n\n"
        "Теперь введите цену товара в баллах:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_CREATE_PRODUCT_PRICE

async def handle_delete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора задания для удаления и подтверждение"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel_delete_task":
        await query.edit_message_text("❌ Удаление задания отменено.", reply_markup=get_admin_keyboard())
        return

    if data.startswith("del_task_"):
        task_id = data.split("_")[2]
        tasks = load_tasks()

        if task_id not in tasks:
            await query.edit_message_text("❌ Задание не найдено.", reply_markup=get_admin_keyboard())
            return

        task = tasks[task_id]
        desc_preview = (task['description'][:30] + '...') if len(task['description']) > 30 else task['description']

        # Кнопки подтверждения
        confirm_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_del_task_{task_id}"),
                InlineKeyboardButton("❌ Нет", callback_data="cancel_delete_task")
            ]
        ])

        await query.edit_message_text(
            f"⚠️ <b>Подтверждение удаления</b>\n"
            f"🎯 Задание #{task_id}\n"
            f"📝 {desc_preview}\n"
            f"⭐ Награда: {task['points']} баллов\n\n"
            f"<b>Вы уверены?</b> Это действие необратимо.",
            parse_mode='HTML',
            reply_markup=confirm_keyboard
        )

async def handle_confirm_delete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальное удаление задания"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_task_"):
        task_id = data.split("_")[3]
        tasks = load_tasks()

        if task_id not in tasks:
            await query.edit_message_text("❌ Задание уже удалено или не найдено.")
            return

        task_info = tasks[task_id]
        del tasks[task_id]
        save_tasks(tasks)

        # Удаляем все связанные отправки
        submissions = load_submissions()
        to_delete = [sid for sid, sub in submissions.items() if sub.get('task_id') == task_id]
        for sid in to_delete:
            del submissions[sid]
        save_submissions(submissions)

        await query.edit_message_text(
            f"✅ <b>Задание удалено!</b>\n"
            f"🗑️ ID: #{task_id}\n"
            f"📝 Описание: {task_info['description']}\n"
            f"⭐ Баллы: {task_info['points']}",
            parse_mode='HTML'
        )
        
async def admin_create_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка цены товара и запрос количества"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление товара отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    try:
        price = int(text)
        if price <= 0:
            await update.message.reply_text(
                "❌ Цена должна быть положительным числом. Попробуйте еще раз:"
            )
            return ADMIN_CREATE_PRODUCT_PRICE
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите целое число. Попробуйте еще раз:"
        )
        return ADMIN_CREATE_PRODUCT_PRICE

    # Сохраняем цену
    context.user_data['product_price'] = price

    await update.message.reply_text(
        f"📦 <b>Название товара:</b> {context.user_data['product_name']}\n"
        f"📝 <b>Описание:</b> {context.user_data['product_description']}\n"
        f"💰 <b>Цена:</b> {price} баллов\n\n"
        "Теперь введите количество товара (0 - без ограничений):",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_SET_PRODUCT_QUANTITY

async def admin_set_product_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка количества товара и сохранение"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление товара отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    try:
        quantity = int(text)
        if quantity < 0:
            await update.message.reply_text(
                "❌ Количество не может быть отрицательным. Попробуйте еще раз:"
            )
            return ADMIN_SET_PRODUCT_QUANTITY
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите целое число. Попробуйте еще раз:"
        )
        return ADMIN_SET_PRODUCT_QUANTITY

    product_name = context.user_data.get('product_name')
    product_description = context.user_data.get('product_description')
    product_price = context.user_data.get('product_price')

    if not product_name or not product_description or product_price is None:
        await update.message.reply_text(
            "❌ Ошибка: данные товара не найдены. Начните заново.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем товар
    products = load_products()
    product_id = str(generate_product_id(products))

    products[product_id] = {
        'name': product_name,
        'description': product_description,
        'price': product_price,
        'quantity': quantity,
        'sold': 0,
        'created_at': datetime.now().isoformat(),
        'created_by': update.effective_user.id
    }
    save_products(products)

    # Очищаем контекст
    context.user_data.pop('product_name', None)
    context.user_data.pop('product_description', None)
    context.user_data.pop('product_price', None)

    quantity_text = "без ограничений" if quantity == 0 else f"{quantity} шт."

    await update.message.reply_text(
        f"✅ <b>Товар успешно добавлен!</b>\n\n"
        f"📦 Товар #{product_id}\n"
        f"🎁 Название: {product_name}\n"
        f"📝 Описание: {product_description}\n"
        f"💰 Цена: {product_price} баллов\n"
        f"📦 Количество: {quantity_text}\n\n"
        f"Теперь пользователи могут покупать этот товар!",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def admin_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление товара с inline кнопками"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    products = load_products()

    if not products:
        await update.message.reply_text(
            "📭 Товаров для удаления нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    # Создаем inline клавиатуру с товарами
    keyboard = []
    for product_id, product in products.items():
        quantity_text = "∞" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."
        button_text = f"#{product_id} - {product['name'][:20]} ({quantity_text})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_product_{product_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="delete_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🗑️ <b>Удаление товара</b>\n\n"
        "Выберите товар для удаления:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_delete_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback для удаления товара"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "delete_cancel":
        await query.edit_message_text(
            "❌ Удаление товара отменено.",
            reply_markup=get_admin_keyboard()
        )
        return

    if data.startswith("delete_product_"):
        product_id = data.split('_')[2]

        products = load_products()

        if product_id not in products:
            await query.edit_message_text(
                "❌ Товар не найден.",
                reply_markup=get_admin_keyboard()
            )
            return

        product = products[product_id]
        quantity_text = "без ограничений" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."

        # Создаем клавиатуру для подтверждения удаления
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{product_id}"),
                InlineKeyboardButton("❌ Отменить", callback_data="delete_cancel_final")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"⚠️ <b>Подтверждение удаления</b>\n\n"
            f"📦 Товар #{product_id}\n"
            f"🎁 Название: {product['name']}\n"
            f"📝 Описание: {product['description']}\n"
            f"💰 Цена: {product['price']} баллов\n"
            f"📦 Количество: {quantity_text}\n"
            f"🛒 Продано: {product.get('sold', 0)} шт.\n\n"
            f"<b>Вы уверены, что хотите удалить этот товар?</b>\n"
            f"Эта операция необратима!",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def handle_confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения удаления товара"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("confirm_delete_"):
        product_id = data.split('_')[2]

        products = load_products()

        if product_id not in products:
            await query.edit_message_text(
                "❌ Товар не найден.",
                reply_markup=get_admin_keyboard()
            )
            return

        product_info = products[product_id]

        # Удаляем товар
        del products[product_id]
        save_products(products)

        await query.edit_message_text(
            f"✅ <b>Товар успешно удален!</b>\n\n"
            f"🗑️ Удален товар #{product_id}\n"
            f"🎁 Название: {product_info['name']}\n"
            f"💰 Цена: {product_info['price']} баллов\n\n"
            f"Товар больше не доступен для покупки.",
            parse_mode='HTML'
        )

async def handle_delete_cancel_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка окончательной отмены удаления"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "❌ Удаление товара отменено.",
        parse_mode='HTML'
    )

async def admin_products_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех товаров"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    products = load_products()

    if not products:
        await update.message.reply_text(
            "📭 Товаров пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    products_text = "🛍️ <b>Список товаров:</b>\n\n"

    for product_id, product in products.items():
        quantity_text = "∞" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."
        sold_text = f" | 🛒 Продано: {product.get('sold', 0)} шт." if product.get('quantity', 0) > 0 else ""

        products_text += (
            f"📦 <b>Товар #{product_id}</b>\n"
            f"🎁 {product['name']}\n"
            f"📝 {product['description']}\n"
            f"💰 Цена: {product['price']} баллов\n"
            f"📦 В наличии: {quantity_text}{sold_text}\n"
            f"📅 Добавлен: {product.get('created_at', 'Неизвестно')[:10]}\n"
            f"────────────────────\n"
        )

    await update.message.reply_text(
        products_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_review_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр выбранного задания для оценки"""
    text = update.message.text
    if text == "🔙 Назад":
        return await admin_pending_submissions(update, context)
    
    try:
        submission_id = text.split('#')[1].split(' - ')[0]
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора задания. Попробуйте еще раз:",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END
        
    submissions = load_submissions()
    if submission_id not in submissions:
        await update.message.reply_text(
            "❌ Отправка не найдена.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END
        
    submission = submissions[submission_id]
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"approve_{submission_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{submission_id}")
        ]
    ])
    
    submission_info = (
        f"📨 <b>Задание на проверке</b>\n"
        f"👤 <b>Пользователь:</b> {submission['user_name']} (ID: #{submission['user_unique_id']})\n"
        f"🎯 <b>Задание:</b> {submission['task_description']}\n"
        f"⭐ <b>Баллы:</b> {submission['task_points']}\n"
        f"📎 <b>Файлов отправлено:</b> {len(submission.get('files', []))}\n"
        f"🕒 <b>Время отправки:</b> {submission['submission_time'][:16]}"
    )
    
    if submission.get('text_content'):
        submission_info += f"\n📝 <b>Текст ответа:</b>\n{submission['text_content'][:500]}" + ("..." if len(submission['text_content']) > 500 else "")
        
    back_keyboard = ReplyKeyboardMarkup([[KeyboardButton("🔙 Назад")]], resize_keyboard=True)
    
    # Отправляем все файлы
    files = submission.get('files', [])
    for i, file_data in enumerate(files):
        try:
            if file_data['type'] == 'photo':
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=file_data['file_id'],
                    caption=f"📸 Фото {i+1}/{len(files)}" + (f": {file_data.get('caption', '')}" if file_data.get('caption') else ""),
                    parse_mode='HTML'
                )
            elif file_data['type'] == 'document':
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=file_data['file_id'],
                    caption=f"📄 Документ {i+1}/{len(files)}" + (f": {file_data.get('caption', '')}" if file_data.get('caption') else ""),
                    parse_mode='HTML'
                )
            elif file_data['type'] == 'video':
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=file_data['file_id'],
                    caption=f"🎥 Видео {i+1}/{len(files)}" + (f": {file_data.get('caption', '')}" if file_data.get('caption') else ""),
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Не удалось отправить файл {i+1} для проверки: {e}")
    
    # Отправляем информацию о задании
    await update.message.reply_text(
        submission_info,
        parse_mode='HTML',
        reply_markup=keyboard
    )
        
    await update.message.reply_text(
        "Используйте кнопки выше для оценки задания. Кнопка 'Назад' вернет к списку заданий:",
        reply_markup=back_keyboard
    )
    return ConversationHandler.END

async def handle_task_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отправленного задания"""
    user_id = str(update.effective_user.id)
    users = load_users()
    tasks = load_tasks()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    task_id = context.user_data.get('selected_task')
    if not task_id or task_id not in tasks:
        await update.message.reply_text(
            "❌ Ошибка: задание не выбрано.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    user_data = users[user_id]
    task = tasks[task_id]

    # Сохраняем отправку задания
    submissions = load_submissions()
    submission_id = str(generate_task_id(submissions))

    # Определяем тип контента
    content_type = "text"
    content = update.message.text or ""
    file_id = None

    if update.message.photo:
        content_type = "photo"
        content = "Фото"
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        content_type = "document"
        content = update.message.document.file_name
        file_id = update.message.document.file_id
    elif update.message.video:
        content_type = "video"
        content = "Видео"
        file_id = update.message.video.file_id

    submissions[submission_id] = {
        'user_id': user_id,
        'user_name': f"{user_data['first_name']} {user_data['surname']}",
        'user_unique_id': user_data['unique_id'],
        'task_id': task_id,
        'task_title': task.get('title', 'Без названия'),
        'task_description': task['description'],
        'task_points': task['points'],
        'task_type': task.get('type', 'once'),
        'content_type': content_type,
        'content': content,
        'file_id': file_id,
        'submission_time': datetime.now().isoformat(),
        'status': 'pending'
    }
    save_submissions(submissions)

    # Отправляем уведомление администраторам
    for admin_id in ADMIN_IDS:
        try:
            admin_message = (
                f"📨 <b>Новое задание на проверку!</b>\n\n 💡 <i>Для проверки перейдите в панель администратора → '📨 Проверка заданий'</i>"
            )

            if content_type == "photo":
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=admin_message,
                    parse_mode='HTML'
                )
            elif content_type == "document":
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=file_id,
                    caption=admin_message,
                    parse_mode='HTML'
                )
            elif content_type == "video":
                await context.bot.send_video(
                    chat_id=admin_id,
                    video=file_id,
                    caption=admin_message,
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message + f"\n\n📝 <b>Ответ:</b> {content}",
                    parse_mode='HTML'
                )

        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    await update.message.reply_text(
        "✅ Задание успешно отправлено на проверку!\n\n"
        "Ожидайте решения администратора. Вы получите уведомление, когда задание будет проверено.",
        reply_markup=get_main_keyboard()
    )

    return ConversationHandler.END

async def handle_submission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от кнопок принятия/отклонения"""
    query = update.callback_query
    await query.answer()
    data = query.data
    submission_id = data.split('_')[1]
    action = data.split('_')[0]
    submissions = load_submissions()
    users = load_users()
    
    if submission_id not in submissions:
        await query.edit_message_text("❌ Отправка не найдена.")
        return

    submission = submissions[submission_id]
    user_id = submission['user_id']
    
    if action == 'approve':
        if user_id in users:
            # Начисляем баллы
            users[user_id]['points'] += submission['task_points']
            # И добавляем к общему заработку
            users[user_id]['total_earned'] += submission['task_points']
            save_users(users)
            submission['status'] = 'approved'
            save_submissions(submissions)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 <b>Ваше задание принято!</b>\n"
                         f"🎯 Задание: {submission['task_description']}\n"
                         f"⭐ Начислено баллов: +{submission['task_points']}\n"
                         f"💰 Теперь у вас: {users[user_id]['points']} баллов\n"
                         f"Поздравляем! 🎊",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")
            await query.edit_message_text(
                f"✅ <b>Задание принято!</b>\n"
                f"👤 Пользователь: {submission['user_name']}\n"
                f"🎯 Задание: {submission['task_description']}\n"
                f"⭐ Начислено баллов: {submission['task_points']}\n"
                f"💰 Новый баланс: {users[user_id]['points']}",
                parse_mode='HTML'
            )
    elif action == 'reject':
        submission['status'] = 'rejected'
        save_submissions(submissions)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ <b>Ваше задание отклонено</b>\n"
                     f"🎯 Задание: {submission['task_description']}\n"
                     f"💡 Попробуйте выполнить задание еще раз или выберите другое задание.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")
        await query.edit_message_text(
            f"❌ <b>Задание отклонено</b>\n"
            f"👤 Пользователь: {submission['user_name']}\n"
            f"🎯 Задание: {submission['task_description']}",
            parse_mode='HTML'
        )

    await query.message.reply_text(
        "✅ Задание обработано. Нажмите «📨 Проверка заданий» в меню, чтобы продолжить.",
        reply_markup=get_admin_keyboard()
    )
    return ConversationHandler.END

async def admin_pending_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список заданий на проверке с возможностью выбора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    submissions = load_submissions()
    pending_subs = {k: v for k, v in submissions.items() if v['status'] == 'pending'}

    if not pending_subs:
        await update.message.reply_text(
            "✅ Заданий на проверке нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Создаем клавиатуру с заданиями на проверке
    keyboard = []
    for sub_id, submission in pending_subs.items():
        keyboard.append([KeyboardButton(
            f"#{sub_id} - {submission['user_name']} - {submission['task_description'][:30]}..."
        )])

    keyboard.append([KeyboardButton("🔙 Назад")])

    await update.message.reply_text(
        f"📨 <b>Задания на проверке:</b> {len(pending_subs)}\n\n"
        "Выберите задание для оценки:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ADMIN_REVIEW_SELECT

async def submit_task_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора задания"""
    text = update.message.text
    if text == "🔙 Отмена":
        await update.message.reply_text("❌ Отправка задания отменена.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    try:
        task_id = text.split('#')[1].split(' - ')[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Ошибка выбора задания. Попробуйте еще раз:", reply_markup=get_main_keyboard())
        return USER_SELECT_TASK

    tasks = load_tasks()
    if task_id not in tasks:
        await update.message.reply_text("❌ Задание не найдено.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    # Проверяем возможность выполнения задания
    user_id = str(update.effective_user.id)
    task = tasks[task_id]
    
    can_submit, message = await check_task_availability(user_id, task_id, task)
    if not can_submit:
        await update.message.reply_text(
            message,
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    context.user_data['selected_task'] = task_id
    # Инициализируем список файлов
    context.user_data['files'] = []
    context.user_data['text_content'] = ""

    task_type = task.get('type', 'once')
    type_text = "одноразовое" if task_type == "once" else "ежедневное"

    await update.message.reply_text(
        f"📤 <b>Отправка задания:</b>\n"
        f"🎯 Задание #{task_id} ({type_text})\n"
        f"📝 <b>Название:</b> {task.get('title', 'Без названия')}\n"
        f"📄 <b>Описание:</b> {task['description']}\n"
        f"⭐ <b>Награда:</b> {task['points']} баллов\n\n"
        f"📎 Вы можете прикрепить несколько файлов, фото, видео или написать текстовый ответ.\n"
        f"Когда закончите, нажмите кнопку <b>✅ Завершить отправку</b>",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✅ Завершить отправку")],
            [KeyboardButton("🔙 Отмена")]
        ], resize_keyboard=True)
    )
    return USER_SEND_TASK_CONTENT
    
async def check_task_availability(user_id: str, task_id: str, task: dict) -> tuple:
    """Проверяет, может ли пользователь выполнить задание"""
    submissions = load_submissions()
    task_type = task.get('type', 'once')
    
    if task_type == 'once':
        # Проверяем, есть ли уже принятая отправка этого задания
        for submission in submissions.values():
            if (submission['user_id'] == user_id and 
                submission['task_id'] == task_id and 
                submission['status'] == 'approved'):
                return False, "❌ Вы уже выполнили это одноразовое задание!"
                
    elif task_type == 'daily':
        # Проверяем отправки за последние 24 часа
        now = datetime.now()
        for submission in submissions.values():
            if (submission['user_id'] == user_id and 
                submission['task_id'] == task_id and 
                submission['status'] == 'approved'):
                
                submission_time = datetime.fromisoformat(submission['submission_time'])
                time_diff = now - submission_time
                
                if time_diff.total_seconds() < 24 * 3600:
                    hours_left = 24 - (time_diff.total_seconds() / 3600)
                    return False, (
                        f"⏰ Вы уже выполняли это задание сегодня!\n"
                        f"Следующая попытка будет доступна через {hours_left:.1f} часов"
                    )
    
    return True, ""

async def handle_task_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка контента задания (можно несколько файлов)"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text("❌ Отправка задания отменена.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    if text == "✅ Завершить отправку":
        # Проверяем, есть ли хотя бы что-то отправленное
        files = context.user_data.get('files', [])
        text_content = context.user_data.get('text_content', '')
        
        if not files and not text_content:
            await update.message.reply_text(
                "❌ Вы не отправили ни файлов, ни текста. Пожалуйста, отправьте хотя бы что-то или отмените отправку.",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("✅ Завершить отправку")],
                    [KeyboardButton("🔙 Отмена")]
                ], resize_keyboard=True)
            )
            return USER_SEND_TASK_CONTENT
        
        # Переходим к финальной отправке
        return await finalize_task_submission(update, context)

    user_id = str(update.effective_user.id)
    users = load_users()
    tasks = load_tasks()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    task_id = context.user_data.get('selected_task')
    if not task_id or task_id not in tasks:
        await update.message.reply_text(
            "❌ Ошибка: задание не выбрано.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    # Обрабатываем контент
    files = context.user_data.get('files', [])
    
    # Обработка фото
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        files.append({
            'type': 'photo',
            'file_id': file_id,
            'caption': update.message.caption or ''
        })
        context.user_data['files'] = files
        await update.message.reply_text(
            f"✅ Фото добавлено. Отправлено файлов: {len(files)}\n"
            f"Продолжайте отправлять файлы или нажмите <b>✅ Завершить отправку</b>",
            parse_mode='HTML'
        )
        
    # Обработка документа
    elif update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name
        files.append({
            'type': 'document',
            'file_id': file_id,
            'file_name': file_name,
            'caption': update.message.caption or ''
        })
        context.user_data['files'] = files
        await update.message.reply_text(
            f"✅ Документ '{file_name}' добавлен. Отправлено файлов: {len(files)}\n"
            f"Продолжайте отправлять файлы или нажмите <b>✅ Завершить отправку</b>",
            parse_mode='HTML'
        )
        
    # Обработка видео
    elif update.message.video:
        file_id = update.message.video.file_id
        files.append({
            'type': 'video',
            'file_id': file_id,
            'caption': update.message.caption or ''
        })
        context.user_data['files'] = files
        await update.message.reply_text(
            f"✅ Видео добавлено. Отправлено файлов: {len(files)}\n"
            f"Продолжайте отправлять файлы или нажмите <b>✅ Завершить отправку</b>",
            parse_mode='HTML'
        )
        
    # Обработка текста
    elif update.message.text and text not in ["✅ Завершить отправку", "🔙 Отмена"]:
        text_content = context.user_data.get('text_content', '')
        if text_content:
            text_content += "\n\n" + text
        else:
            text_content = text
        context.user_data['text_content'] = text_content
        await update.message.reply_text(
            f"✅ Текст добавлен. Длина: {len(text_content)} символов.\n"
            f"Продолжайте отправлять текст или файлы, или нажмите <b>✅ Завершить отправку</b>",
            parse_mode='HTML'
        )

    return USER_SEND_TASK_CONTENT

async def admin_create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания задания"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END
    
    # Очищаем контекст
    context.user_data.pop('task_title', None)
    context.user_data.pop('task_description', None)
    
    await update.message.reply_text(
        "📝 <b>Создание нового задания</b>\n\n"
        "Введите название задания:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )
    return ADMIN_CREATE_TASK_TITLE
    
async def finalize_task_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальная отправка задания со всеми файлами"""
    user_id = str(update.effective_user.id)
    users = load_users()
    tasks = load_tasks()

    task_id = context.user_data.get('selected_task')
    user_data = users[user_id]
    task = tasks[task_id]
    
    files = context.user_data.get('files', [])
    text_content = context.user_data.get('text_content', '')

    # Сохраняем отправку задания
    submissions = load_submissions()
    submission_id = str(generate_task_id(submissions))

    # Определяем тип контента
    if files:
        content_type = "multiple_files"
        if len(files) == 1:
            content_type = files[0]['type']
    else:
        content_type = "text"

    submissions[submission_id] = {
        'user_id': user_id,
        'user_name': f"{user_data['first_name']} {user_data['surname']}",
        'user_unique_id': user_data['unique_id'],
        'task_id': task_id,
        'task_title': task.get('title', 'Без названия'),
        'task_description': task['description'],
        'task_points': task['points'],
        'task_type': task.get('type', 'once'),
        'content_type': content_type,
        'content': text_content,
        'files': files,  # Сохраняем все файлы
        'text_content': text_content,
        'submission_time': datetime.now().isoformat(),
        'status': 'pending'
    }
    save_submissions(submissions)

    # Отправляем уведомление администраторам
    for admin_id in ADMIN_IDS:
        try:
            admin_message = (
                f"📨 <b>Новое задание на проверку!</b>\n\n"
                f"👤 Пользователь: {user_data['first_name']} {user_data['surname']} (ID: #{user_data['unique_id']})\n"
                f"🎯 Задание: {task.get('title', 'Без названия')}\n"
                f"📝 Описание: {task['description']}\n"
                f"⭐ Баллы: {task['points']}\n"
                f"📎 Файлов отправлено: {len(files)}\n"
                f"📝 Текста символов: {len(text_content)}\n\n"
                f"💡 <i>Для проверки перейдите в панель администратора → '📨 Проверка заданий'</i>"
            )

            # Отправляем все файлы по одному
            for i, file_data in enumerate(files):
                try:
                    if file_data['type'] == 'photo':
                        await context.bot.send_photo(
                            chat_id=admin_id,
                            photo=file_data['file_id'],
                            caption=f"📸 Фото {i+1}/{len(files)}" + (f": {file_data['caption']}" if file_data.get('caption') else ""),
                            parse_mode='HTML'
                        )
                    elif file_data['type'] == 'document':
                        await context.bot.send_document(
                            chat_id=admin_id,
                            document=file_data['file_id'],
                            caption=f"📄 Документ {i+1}/{len(files)}" + (f": {file_data['caption']}" if file_data.get('caption') else ""),
                            parse_mode='HTML'
                        )
                    elif file_data['type'] == 'video':
                        await context.bot.send_video(
                            chat_id=admin_id,
                            video=file_data['file_id'],
                            caption=f"🎥 Видео {i+1}/{len(files)}" + (f": {file_data['caption']}" if file_data.get('caption') else ""),
                            parse_mode='HTML'
                        )
                except Exception as e:
                    logger.error(f"Не удалось отправить файл {i+1} администратору {admin_id}: {e}")

            # Отправляем текстовое сообщение
            if text_content:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message + f"\n\n📝 <b>Текст ответа:</b>\n{text_content[:1000]}" + ("..." if len(text_content) > 1000 else ""),
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode='HTML'
                )

        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    # Показываем подтверждение пользователю
    confirmation_text = (
        f"✅ <b>Задание успешно отправлено на проверку!</b>\n\n"
        f"🎯 Задание: {task.get('title', 'Без названия')}\n"
        f"📎 Отправлено файлов: {len(files)}\n"
    )
    
    if text_content:
        confirmation_text += f"📝 Текст ответа: {len(text_content)} символов\n"
    
    confirmation_text += (
        f"\nОжидайте решения администратора. Вы получите уведомление, когда задание будет проверено."
    )

    await update.message.reply_text(
        confirmation_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

    # Очищаем контекст
    context.user_data.pop('selected_task', None)
    context.user_data.pop('files', None)
    context.user_data.pop('text_content', None)

    return ConversationHandler.END
    
async def admin_create_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия задания"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Создание задания отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем название задания
    context.user_data['task_title'] = text

    await update.message.reply_text(
        f"📝 <b>Название задания:</b> {text}\n\n"
        "Теперь введите описание задания:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )
    return ADMIN_CREATE_TASK

async def admin_create_task_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания задания"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Создание задания отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем описание задания
    context.user_data['task_description'] = text

    await update.message.reply_text(
        f"📝 <b>Название задания:</b> {context.user_data['task_title']}\n"
        f"📄 <b>Описание задания:</b> {text}\n\n"
        "Теперь введите количество баллов за выполнение:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )
    return ADMIN_SET_TASK_POINTS

async def admin_set_task_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка баллов для задания и выбор типа"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Создание задания отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    try:
        points = int(text)
        if points <= 0:
            await update.message.reply_text(
                "❌ Количество баллов должно быть положительным числом. Попробуйте еще раз:"
            )
            return ADMIN_SET_TASK_POINTS
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите целое число. Попробуйте еще раз:"
        )
        return ADMIN_SET_TASK_POINTS

    # Сохраняем баллы
    context.user_data['task_points'] = points

    # Создаем клавиатуру для выбора типа задания
    keyboard = [
        [KeyboardButton("✅ Одноразовое задание"), KeyboardButton("🔄 Ежедневное задание")],
        [KeyboardButton("🔙 Отмена")]
    ]

    await update.message.reply_text(
        f"📝 <b>Название задания:</b> {context.user_data['task_title']}\n"
        f"📄 <b>Описание задания:</b> {context.user_data['task_description']}\n"
        f"⭐ <b>Баллы:</b> {points}\n\n"
        "Выберите тип задания:\n\n"
        "✅ <b>Одноразовое</b> - можно выполнить только один раз\n"
        "🔄 <b>Ежедневное</b> - можно выполнять раз в сутки",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ADMIN_CREATE_TASK_TYPE

async def admin_create_task_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа задания и сохранение"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Создание задания отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    if text not in ["✅ Одноразовое задание", "🔄 Ежедневное задание"]:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите тип задания используя кнопки:",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Одноразовое задание"), KeyboardButton("🔄 Ежедневное задание")],
                [KeyboardButton("🔙 Отмена")]
            ], resize_keyboard=True)
        )
        return ADMIN_CREATE_TASK_TYPE

    # Определяем тип задания
    task_type = "once" if text == "✅ Одноразовое задание" else "daily"

    # Получаем данные из контекста
    task_title = context.user_data.get('task_title')
    task_description = context.user_data.get('task_description')
    task_points = context.user_data.get('task_points')

    if not all([task_title, task_description, task_points]):
        await update.message.reply_text(
            "❌ Ошибка: данные задания не найдены. Начните заново.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем задание
    tasks = load_tasks()
    task_id = str(generate_task_id(tasks))

    tasks[task_id] = {
        'title': task_title,
        'description': task_description,
        'points': task_points,
        'type': task_type,
        'created_at': datetime.now().isoformat(),
        'created_by': update.effective_user.id
    }
    save_tasks(tasks)

    type_text = "одноразовое" if task_type == "once" else "ежедневное"

    await update.message.reply_text(
        f"✅ <b>Задание успешно создано!</b>\n\n"
        f"🎯 Задание #{task_id}\n"
        f"📝 Название: {task_title}\n"
        f"📄 Описание: {task_description}\n"
        f"⭐ Баллы: {task_points}\n"
        f"🔄 Тип: {type_text}\n\n"
        f"Теперь пользователи могут видеть это задание и отправлять его на проверку.",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    # Очищаем контекст
    context.user_data.pop('task_title', None)
    context.user_data.pop('task_description', None)
    context.user_data.pop('task_points', None)

    return ConversationHandler.END

async def admin_tasks_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех заданий"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    tasks = load_tasks()

    if not tasks:
        await update.message.reply_text(
            "📭 Заданий пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    tasks_text = "📋 <b>Список заданий:</b>\n\n"

    for task_id, task in tasks.items():
        task_type = task.get('type', 'once')
        type_icon = "✅" if task_type == "once" else "🔄"
        type_text = "Одноразовое" if task_type == "once" else "Ежедневное"
        
        tasks_text += (
            f"{type_icon} <b>Задание #{task_id}</b> ({type_text})\n"
            f"📝 <b>Название:</b> {task.get('title', 'Без названия')}\n"
            f"📄 <b>Описание:</b> {task['description']}\n"
            f"⭐ <b>Баллы:</b> {task['points']}\n"
            f"📅 <b>Создано:</b> {task.get('created_at', 'Неизвестно')[:10]}\n"
            f"────────────────────\n"
        )

    await update.message.reply_text(
        tasks_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def submit_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        await update.message.reply_text("❌ Вы не зарегистрированы. Используйте команду /start для регистрации.")
        return ConversationHandler.END

    tasks = load_tasks()
    if not tasks:
        await update.message.reply_text("📭 На данный момент активных заданий нет.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    keyboard = []
    for task_id, task in tasks.items():
        task_type = task.get('type', 'once')
        type_icon = "✅" if task_type == "once" else "🔄"
        
        # Проверяем доступность задания
        can_submit, _ = await check_task_availability(user_id, task_id, task)
        status_icon = "🟢" if can_submit else "🔴"
        
        button_text = f"{status_icon} {type_icon} Задание #{task_id} - {task.get('title', 'Без названия')}"
        keyboard.append([KeyboardButton(button_text)])
    
    keyboard.append([KeyboardButton("🔙 Отмена")])

    await update.message.reply_text(
        "📋 <b>Выберите задание:</b>\n\n"
        "🟢 - доступно\n"
        "🔴 - недоступно\n"
        "✅ - одноразовое\n"
        "🔄 - ежедневное\n\n"
        "Нажмите на задание, которое хотите отправить на проверку:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return USER_SELECT_TASK

# ФУНКЦИИ ДЛЯ РЕДАКТИРОВАНИЯ ID

async def admin_fix_id_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса редактирования ID"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Создаем клавиатуру с пользователями
    keyboard = []
    for uid, user_data in users.items():
        keyboard.append([KeyboardButton(
            f"#{user_data['unique_id']} - {user_data['first_name']} {user_data['surname']}"
        )])

    keyboard.append([KeyboardButton("🔙 Отмена")])

    await update.message.reply_text(
        "👥 <b>Выберите пользователя:</b>\n\n"
        "Нажмите на пользователя, которому хотите изменить ID:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ADMIN_FIX_ID_SELECT_USER

async def admin_fix_id_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пользователя для смены ID"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Изменение ID отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Извлекаем ID пользователя из текста
    try:
        user_unique_id = int(text.split('#')[1].split(' - ')[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора пользователя. Попробуйте еще раз:",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    users = load_users()
    selected_user = None

    for uid, user_data in users.items():
        if user_data['unique_id'] == user_unique_id:
            selected_user = user_data
            selected_user['telegram_id'] = uid
            break

    if not selected_user:
        await update.message.reply_text(
            "❌ Пользователь не найден.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем выбранного пользователя в контексте
    context.user_data['selected_user'] = selected_user

    await update.message.reply_text(
        f"👤 <b>Выбран пользователь:</b>\n\n"
        f"📝 Имя: {selected_user['first_name']}\n"
        f"📝 Фамилия: {selected_user['surname']}\n"
        f"🆔 Текущий ID: #{selected_user['unique_id']}\n\n"
        "Введите новый ID (только число):",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_FIX_ID_SET_NEW

async def admin_fix_id_set_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка нового ID для пользователя"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Изменение ID отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    try:
        new_id = int(text)
        if new_id <= 0:
            await update.message.reply_text(
                "❌ ID должен быть положительным числом. Попробуйте еще раз:"
            )
            return ADMIN_FIX_ID_SET_NEW
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите целое число. Попробуйте еще раз:"
        )
        return ADMIN_FIX_ID_SET_NEW

    selected_user = context.user_data.get('selected_user')
    if not selected_user:
        await update.message.reply_text(
            "❌ Ошибка: пользователь не выбран.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    users = load_users()

    # Проверяем, не занят ли новый ID другим пользователем
    for uid, user_data in users.items():
        if user_data['unique_id'] == new_id and uid != selected_user['telegram_id']:
            await update.message.reply_text(
                f"❌ ID #{new_id} уже занят пользователем {user_data['first_name']} {user_data['surname']}.\n"
                f"Пожалуйста, выберите другой ID:",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
            )
            return ADMIN_FIX_ID_SET_NEW

    # Обновляем ID пользователя
    old_id = selected_user['unique_id']
    users[selected_user['telegram_id']]['unique_id'] = new_id
    save_users(users)

    await update.message.reply_text(
        f"✅ <b>ID успешно изменен!</b>\n\n"
        f"👤 Пользователь: {selected_user['first_name']} {selected_user['surname']}\n"
        f"🆔 Старый ID: #{old_id}\n"
        f"🆕 Новый ID: #{new_id}",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель администратора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ У вас нет доступа к этой команде."
        )
        return

    await update.message.reply_text(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех пользователей"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    users_list = "👥 <b>Список пользователей:</b>\n\n"

    for uid, user_data in users.items():
        users_list += (
            f"👤 {user_data['first_name']} {user_data['surname']}\n"
            f"🆔 ID: #{user_data['unique_id']}\n"
            f"⭐ Баллы: {user_data['points']}\n"
            f"📅 Регистрация: {user_data.get('registered_at', 'Неизвестно')[:10]}\n"
            f"────────────────────\n"
        )

    await update.message.reply_text(
        users_list,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_add_points_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса добавления баллов"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    users = load_users()
    
    if not users:
        await update.message.reply_text(
            "📭 Пользователей пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Создаем клавиатуру с пользователями
    keyboard = []
    for uid, user_data in users.items():
        keyboard.append([KeyboardButton(
            f"#{user_data['unique_id']} - {user_data['first_name']} {user_data['surname']} ({user_data['points']} баллов)"
        )])

    keyboard.append([KeyboardButton("🔙 Отмена")])

    await update.message.reply_text(
        "👥 <b>Выберите пользователя:</b>\n\n"
        "Нажмите на пользователя, которому хотите добавить баллы:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ADMIN_SELECT_USER

async def admin_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пользователя"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление баллов отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Извлекаем ID пользователя из текста
    try:
        user_unique_id = int(text.split('#')[1].split(' - ')[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора пользователя. Попробуйте еще раз:",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    users = load_users()
    selected_user = None

    for uid, user_data in users.items():
        if user_data['unique_id'] == user_unique_id:
            selected_user = user_data
            selected_user['telegram_id'] = uid
            break

    if not selected_user:
        await update.message.reply_text(
            "❌ Пользователь не найден.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем выбранного пользователя в контексте
    context.user_data['selected_user'] = selected_user

    await update.message.reply_text(
        f"👤 <b>Выбран пользователь:</b>\n\n"
        f"📝 Имя: {selected_user['first_name']}\n"
        f"📝 Фамилия: {selected_user['surname']}\n"
        f"🆔 ID: #{selected_user['unique_id']}\n"
        f"⭐ Текущие баллы: {selected_user['points']}\n\n"
        "Введите количество баллов для добавления:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_ADD_POINTS

async def admin_add_points_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение добавления баллов"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление баллов отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    try:
        points = int(text)
        if points <= 0:
            await update.message.reply_text(
                "❌ Количество баллов должно быть положительным числом. Попробуйте еще раз:"
            )
            return ADMIN_ADD_POINTS
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите целое число. Попробуйте еще раз:"
        )
        return ADMIN_ADD_POINTS

    selected_user = context.user_data.get('selected_user')
    if not selected_user:
        await update.message.reply_text(
            "❌ Ошибка: пользователь не выбран.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    users = load_users()
    telegram_id = selected_user['telegram_id']

    if telegram_id in users:
        users[telegram_id]['points'] += points
        # И добавляем к общему заработку
        users[telegram_id]['total_earned'] += points
        save_users(users)

        new_points = users[telegram_id]['points']

        await update.message.reply_text(
            f"✅ <b>Баллы успешно добавлены!</b>\n\n"
            f"👤 Пользователь: {selected_user['first_name']} {selected_user['surname']}\n"
            f"🆔 ID: #{selected_user['unique_id']}\n"
            f"⭐ Добавлено баллов: +{points}\n"
            f"💰 Новый баланс: {new_points}",
            parse_mode='HTML',
            reply_markup=get_admin_keyboard()
        )

        # Оповещаем пользователя о начислении баллов
        try:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=f"🎉 <b>Вам начислены баллы!</b>\n\n"
                     f"⭐ Добавлено: +{points} баллов\n"
                     f"💰 Теперь у вас: {new_points} баллов\n\n"
                     f"Спасибо за участие!",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление пользователю {telegram_id}: {e}")

    else:
        await update.message.reply_text(
            "❌ Пользователь не найден в базе данных.",
            reply_markup=get_admin_keyboard()
        )

    return ConversationHandler.END

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика для администратора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    users = load_users()
    tasks = load_tasks()
    submissions = load_submissions()

    total_users = len(users)
    total_points = sum(user['points'] for user in users.values())
    total_tasks = len(tasks)

    pending_subs = len([s for s in submissions.values() if s['status'] == 'pending'])
    approved_subs = len([s for s in submissions.values() if s['status'] == 'approved'])
    rejected_subs = len([s for s in submissions.values() if s['status'] == 'rejected'])

    stats_text = (
        "📊 <b>Статистика системы</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"⭐ Всего баллов в системе: {total_points}\n"
        f"📈 Среднее количество баллов: {total_points / total_users if total_users > 0 else 0:.1f}\n\n"
        f"📋 Всего заданий: {total_tasks}\n"
        f"📨 Отправок на проверке: {pending_subs}\n"
        f"✅ Принятых заданий: {approved_subs}\n"
        f"❌ Отклоненных заданий: {rejected_subs}"
    )

    await update.message.reply_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_reset_users_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса сброса пользователей"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей и так нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Показываем подтверждение с информацией
    users_count = len(users)
    total_points = sum(user['points'] for user in users.values())

    confirmation_text = (
        f"⚠️ <b>ВНИМАНИЕ! ОПАСНАЯ ОПЕРАЦИЯ!</b>\n\n"
        f"Вы собираетесь удалить ВСЕХ пользователей:\n"
        f"👥 Количество пользователей: {users_count}\n"
        f"⭐ Всего баллов в системе: {total_points}\n\n"
        f"<b>Эта операция необратима!</b>\n\n"
        f"Для подтверждения введите: <code>ПОДТВЕРЖДАЮ СБРОС</code>\n"
        f"Для отмены нажмите кнопку \"🔙 Отмена\""
    )

    keyboard = [[KeyboardButton("🔙 Отмена")]]

    await update.message.reply_text(
        confirmation_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ADMIN_CONFIRM_RESET

async def admin_reset_users_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение сброса пользователей"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Сброс пользователей отменен.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    if text != "ПОДТВЕРЖДАЮ СБРОС":
        await update.message.reply_text(
            "❌ Для подтверждения сброса необходимо ввести точную фразу: <code>ПОДТВЕРЖДАЮ СБРОС</code>\n\n"
            "Для отмены нажмите кнопку \"🔙 Отмена\"",
            parse_mode='HTML'
        )
        return ADMIN_CONFIRM_RESET

    # Сохраняем информацию о сбросе для логов
    users = load_users()
    users_count = len(users)
    total_points = sum(user['points'] for user in users.values())

    # Сбрасываем пользователей
    save_users({})

    # Также сбрасываем задания, отправки и заказы
    save_tasks({})
    save_submissions({})
    save_orders({})

    logger.warning(
        f"Администратор {update.effective_user.id} сбросил всех пользователей. Удалено: {users_count} пользователей, {total_points} баллов")

    await update.message.reply_text(
        f"✅ <b>Сброс выполнен успешно!</b>\n\n"
        f"🗑️ Удалено пользователей: {users_count}\n"
        f"⭐ Удалено баллов: {total_points}\n"
        f"📋 Очищены задания и заказы\n\n"
        f"Система полностью сброшена.",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    user_id = update.effective_user.id
    users = load_users()
    text = update.message.text

    # Проверка для обычных пользователей
    if str(user_id) not in users and text in ["👤 Профиль", "🛍️ Магазин", "📊 Рейтинг участников", "📤 Отправить задание", "👨‍💼 Панель администратора"]:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы. Используйте команду /start для регистрации."
        )
        return

    # Обработка кнопок главного меню
    if text == "👤 Профиль":
        await profile(update, context)
    elif text == "🛍️ Магазин":
        await shop(update, context)
    elif text == "📊 Рейтинг участников":
        await show_rating(update, context)
    elif text == "📤 Отправить задание":
        await submit_task_start(update, context)
    elif text == "👨‍💼 Панель администратора":
        await admin_panel(update, context)

    # Обработка кнопок администратора
    elif text == "👥 Список пользователей":
        await admin_users_list(update, context)
    elif text == "⭐ Добавить баллы":
        await admin_add_points_start(update, context)
    elif text == "📝 Создать задание":
        await admin_create_task_start(update, context)
    elif text == "📋 Список заданий":
        await admin_tasks_list(update, context)
    elif text == "📨 Проверка заданий":
        await admin_pending_submissions(update, context)
    elif text == "🛍️ Добавить товар":
        await admin_create_product_start(update, context)
    elif text == "📦 Список товаров":
        await admin_products_list(update, context)
    elif text == "🆔 Исправить ID":
        await admin_fix_id_start(update, context)
    elif text == "🗑️ Сбросить пользователей":
        await admin_reset_users_start(update, context)
    elif text == "🗑️ Удалить товар":
        await admin_delete_product(update, context)
    elif text == "🗑️ Удалить задание":
        await admin_delete_task(update, context)
    elif text == "📊 Статистика":
        await admin_stats(update, context)

    elif text == "🔙 Главное меню":
        await update.message.reply_text(
            "🔙 Вы вернулись в главное меню.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
    return ConversationHandler.END
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена для обычных пользователей"""
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard(update.effective_user.id)
    )
    return ConversationHandler.END
    
async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действий администратора"""
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=get_admin_keyboard()
    )
    return ConversationHandler.END

def main():
    """Запуск бота"""
    TOKEN = '8549336941:AAHUqok5bUKTypT-X8UGtXdkih8CDTNnHJ4'
    application = Application.builder().token(TOKEN).build()

    # Инициализация файлов при запуске
    initialize_files()

    user_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_first_name)],
            WAITING_FOR_SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_surname)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    admin_product_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🛍️ Добавить товар$'), admin_create_product_start)],
        states={
            ADMIN_CREATE_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_product_name)],
            ADMIN_CREATE_PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_product_description)],
            ADMIN_CREATE_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_product_price)],
            ADMIN_SET_PRODUCT_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_product_quantity)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )

    user_buy_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🛍️ Магазин$'), shop)],
        states={
            USER_BUY_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_product)],
            USER_CONFIRM_PURCHASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_purchase)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    admin_points_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^⭐ Добавить баллы$'), admin_add_points_start)],
        states={
            ADMIN_SELECT_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_select_user)],
            ADMIN_ADD_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_points_finish)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )

    admin_task_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📝 Создать задание$'), admin_create_task_start)],
        states={
            ADMIN_CREATE_TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_task_title)],
            ADMIN_CREATE_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_task_description)],
            ADMIN_SET_TASK_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_task_points)],
            ADMIN_CREATE_TASK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_task_type)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )

    admin_fix_id_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🆔 Исправить ID$'), admin_fix_id_start)],
        states={
            ADMIN_FIX_ID_SELECT_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_fix_id_select_user)],
            ADMIN_FIX_ID_SET_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_fix_id_set_new)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )

    admin_reset_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🗑️ Сбросить пользователей$'), admin_reset_users_start)],
        states={
            ADMIN_CONFIRM_RESET: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reset_users_confirm)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )

    admin_review_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^📨 Проверка заданий$'), admin_pending_submissions)],
    states={
        ADMIN_REVIEW_SELECT: [
            MessageHandler(filters.Regex('^🔙 Назад$'), lambda u, c: admin_cancel(u, c)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, admin_review_submission)
        ]
    },
    fallbacks=[CommandHandler('cancel', admin_cancel)]
)

    user_task_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^📤 Отправить задание$'), submit_task_start)],
    states={
        USER_SELECT_TASK: [
            MessageHandler(filters.Regex('^🔙 Отмена$'), cancel),
            MessageHandler(filters.TEXT & ~filters.COMMAND, submit_task_select)
        ],
        USER_SEND_TASK_CONTENT: [
            MessageHandler(filters.Regex('^🔙 Отмена$'), cancel),
            MessageHandler(filters.Regex('^✅ Завершить отправку$'), handle_task_content),
            MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO | filters.TEXT, handle_task_content)
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

    application.add_handler(user_conv_handler)
    application.add_handler(admin_points_conv_handler)
    application.add_handler(admin_task_conv_handler)
    application.add_handler(admin_fix_id_conv_handler)
    application.add_handler(admin_review_conv_handler)
    application.add_handler(user_task_conv_handler)
    application.add_handler(admin_product_conv_handler)
    application.add_handler(user_buy_conv_handler)
    application.add_handler(admin_reset_conv_handler)

    application.add_handler(MessageHandler(filters.Regex('^🗑️ Удалить товар$'), admin_delete_product))
    application.add_handler(CallbackQueryHandler(handle_delete_product_callback, pattern='^delete_product_'))
    application.add_handler(CallbackQueryHandler(handle_confirm_delete_callback, pattern='^confirm_delete_'))
    application.add_handler(CallbackQueryHandler(handle_delete_cancel_final, pattern='^delete_cancel_final'))
    application.add_handler(CallbackQueryHandler(handle_delete_product_callback, pattern='^delete_cancel'))
    application.add_handler(MessageHandler(filters.Regex('^🗑️ Удалить задание$'), admin_delete_task))
    application.add_handler(CallbackQueryHandler(handle_delete_task_callback, pattern='^del_task_'))
    application.add_handler(CallbackQueryHandler(handle_confirm_delete_task_callback, pattern='^confirm_del_task_'))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("❌ Удаление отменено.", reply_markup=get_admin_keyboard()), pattern='^cancel_delete_task$'))

    application.add_handler(CallbackQueryHandler(handle_submission_callback))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(MessageHandler(
        filters.Regex(
            r'^(👤 Профиль|🛍️ Магазин|📊 Рейтинг участников|📤 Отправить задание|👨‍💼 Панель администратора|👥 Список пользователей|⭐ Добавить баллы|📝 Создать задание|📋 Список заданий|📨 Проверка заданий|🛍️ Добавить товар|📦 Список товаров|🗑️ Удалить товар|🆔 Исправить ID|🗑️ Сбросить пользователей|📊 Статистика|🔙 Главное меню|🔙 Назад|🔙 Отмена|🛒 Купить товар #\d+|✅ Да, купить товар|❌ Нет, отменить|🔙 Назад к товарам)$'),
        handle_buttons
    ))

    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()



