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

# Настройка логирования для Railway
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
USER_SUBMIT_TASK = 1
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

# Файлы для хранения данных (используем абсолютные пути для Railway)
DATA_DIR = '/data' if os.path.exists('/data') else '.'
DATA_FILE = os.path.join(DATA_DIR, 'users_data.json')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks_data.json')
SUBMISSIONS_FILE = os.path.join(DATA_DIR, 'submissions_data.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products_data.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders_data.json')

# ID администратора (замените на ваш Telegram ID)
ADMIN_IDS = [424081501]  # Замените на ваш реальный ID

# Токен бота из переменных окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8549336941:AAHUqok5bUKTypT-X8UGtXdkih8CDTNnHJ4')

def ensure_data_dir():
    """Создает директорию для данных если её нет"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

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

def load_data(filename):
    """Загрузка данных из файла"""
    try:
        ensure_data_dir()
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
        ensure_data_dir()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных в {filename}: {e}")

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
    """Клавиатура администратора"""
    keyboard = [
        [KeyboardButton("👥 Список пользователей"), KeyboardButton("⭐ Добавить баллы")],
        [KeyboardButton("📝 Создать задание"), KeyboardButton("📋 Список заданий")],
        [KeyboardButton("📨 Проверка заданий"), KeyboardButton("🛍️ Добавить товар")],
        [KeyboardButton("📦 Список товаров"), KeyboardButton("🗑️ Удалить товар")],
        [KeyboardButton("🆔 Исправить ID"), KeyboardButton("🗑️ Сбросить пользователей")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("🔙 Главное меню")]
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
        'points': 0,
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

    # Сортируем пользователей по количеству баллов (от большего к меньшему)
    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1]['points'],
        reverse=True
    )

    rating_text = "📊 <b>Рейтинг участников</b>\n\n"

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
            f"{medal}<b>{index}.</b> {user_name} - {user_data['points']} баллов\n"
        )

        # Добавляем разделитель каждые 5 участников
        if index % 5 == 0 and index < len(sorted_users):
            rating_text += "────────────────────\n"

    # Добавляем статистику
    total_users = len(users)
    total_points = sum(user['points'] for user in users.values())
    average_points = total_points / total_users if total_users > 0 else 0

    rating_text += f"\n📈 <b>Статистика:</b>\n"
    rating_text += f"👥 Всего участников: {total_users}\n"
    rating_text += f"⭐ Всего баллов: {total_points}\n"
    rating_text += f"📊 Средний балл: {average_points:.1f}"

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
        f"⭐ Баллы: {user_data['points']}\n"
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
    user_id = str(update.effective_user.id)
    users = load_users()

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

    user_data = users[user_id]

    # Проверяем достаточно ли баллов (на случай если баланс изменился)
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

    # Списываем баллы
    users[user_id]['points'] -= product['price']
    save_users(users)

    # Обновляем количество товара
    products = load_products()
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
            remaining = "∞" if product.get('quantity', 0) == 0 else product.get('quantity', 0) - products[product_id].get('sold', 0)
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

    remaining_text = "∞" if product.get('quantity', 0) == 0 else product.get('quantity', 0) - products[product_id].get('sold', 0)

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
    """Обработка callback'ов для удаления товара"""
    query = update.callback_query
    await query.answer()

    if query.data == "delete_cancel":
        await query.edit_message_text(
            "❌ Удаление товара отменено.",
            reply_markup=get_admin_keyboard()
        )
        return

    if query.data.startswith("delete_product_"):
        product_id = query.data.split('_')[2]
        products = load_products()

        if product_id not in products:
            await query.edit_message_text(
                "❌ Товар не найден.",
                reply_markup=get_admin_keyboard()
            )
            return

        product = products[product_id]

        # Удаляем товар
        del products[product_id]
        save_products(products)

        quantity_text = "без ограничений" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."

        await query.edit_message_text(
            f"✅ <b>Товар успешно удален!</b>\n\n"
            f"🗑️ Удален товар #{product_id}\n"
            f"🎁 Название: {product['name']}\n"
            f"📝 Описание: {product['description']}\n"
            f"💰 Цена: {product['price']} баллов\n"
            f"📦 Было в наличии: {quantity_text}\n"
            f"🛒 Продано: {product.get('sold', 0)} шт.",
            parse_mode='HTML',
            reply_markup=get_admin_keyboard()
        )

async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех товаров для администратора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    products = load_products()

    if not products:
        await update.message.reply_text(
            "📭 В магазине нет товаров.",
            reply_markup=get_admin_keyboard()
        )
        return

    products_text = "🛍️ <b>Список товаров</b>\n\n"

    for product_id, product in products.items():
        quantity_text = "∞" if product.get('quantity', 0) == 0 else f"{product.get('quantity', 0)} шт."
        remaining = "∞" if product.get('quantity', 0) == 0 else product.get('quantity', 0) - product.get('sold', 0)
        available = remaining == "∞" or remaining > 0

        status_icon = "✅" if available else "❌"
        status_text = "Доступен" if available else "Распродан"

        products_text += (
            f"{status_icon} <b>Товар #{product_id}</b> - {status_text}\n"
            f"🎁 Название: {product['name']}\n"
            f"📝 Описание: {product['description']}\n"
            f"💰 Цена: {product['price']} баллов\n"
            f"📦 Всего: {quantity_text}\n"
            f"🛒 Продано: {product.get('sold', 0)} шт.\n"
            f"🔢 Осталось: {remaining} шт.\n"
            f"📅 Создан: {product.get('created_at', 'Неизвестно')}\n"
            f"────────────────────\n"
        )

    await update.message.reply_text(
        products_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель администратора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к панели администратора.")
        return

    await update.message.reply_text(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список пользователей для администратора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    users_text = "👥 <b>Список пользователей</b>\n\n"

    for telegram_id, user_data in users.items():
        users_text += (
            f"🆔 ID: #{user_data['unique_id']}\n"
            f"👤 Имя: {user_data['first_name']} {user_data['surname']}\n"
            f"⭐ Баллы: {user_data['points']}\n"
            f"📅 Зарегистрирован: {user_data.get('registered_at', 'Неизвестно')}\n"
            f"🔗 Telegram ID: {telegram_id}\n"
            f"────────────────────\n"
        )

    await update.message.reply_text(
        users_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def admin_add_points_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления баллов"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Создаем клавиатуру с пользователями
    keyboard = []
    for telegram_id, user_data in users.items():
        button_text = f"#{user_data['unique_id']} - {user_data['first_name']} {user_data['surname']} ({user_data['points']} баллов)"
        keyboard.append([KeyboardButton(button_text)])

    keyboard.append([KeyboardButton("🔙 Отмена")])

    await update.message.reply_text(
        "⭐ <b>Добавление баллов</b>\n\n"
        "Выберите пользователя:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ADMIN_SELECT_USER

async def admin_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор пользователя для добавления баллов"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Добавление баллов отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Извлекаем ID пользователя из текста
    try:
        unique_id = int(text.split('#')[1].split(' ')[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора пользователя. Попробуйте еще раз:"
        )
        return ADMIN_SELECT_USER

    users = load_users()

    # Находим пользователя по unique_id
    selected_user = None
    selected_user_id = None

    for telegram_id, user_data in users.items():
        if user_data['unique_id'] == unique_id:
            selected_user = user_data
            selected_user_id = telegram_id
            break

    if not selected_user:
        await update.message.reply_text(
            "❌ Пользователь не найден. Попробуйте еще раз:"
        )
        return ADMIN_SELECT_USER

    # Сохраняем выбранного пользователя в контексте
    context.user_data['selected_user_id'] = selected_user_id
    context.user_data['selected_user_name'] = f"{selected_user['first_name']} {selected_user['surname']}"
    context.user_data['selected_user_unique_id'] = unique_id

    await update.message.reply_text(
        f"👤 <b>Выбран пользователь:</b>\n\n"
        f"🆔 ID: #{unique_id}\n"
        f"👤 Имя: {selected_user['first_name']} {selected_user['surname']}\n"
        f"⭐ Текущие баллы: {selected_user['points']}\n\n"
        f"Введите количество баллов для добавления:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_ADD_POINTS

async def admin_add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление баллов пользователю"""
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

    selected_user_id = context.user_data.get('selected_user_id')
    selected_user_name = context.user_data.get('selected_user_name')
    selected_user_unique_id = context.user_data.get('selected_user_unique_id')

    if not selected_user_id:
        await update.message.reply_text(
            "❌ Ошибка: пользователь не найден. Начните заново.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    users = load_users()

    if selected_user_id not in users:
        await update.message.reply_text(
            "❌ Пользователь не найден в базе данных.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Добавляем баллы
    users[selected_user_id]['points'] += points
    save_users(users)

    # Очищаем контекст
    context.user_data.pop('selected_user_id', None)
    context.user_data.pop('selected_user_name', None)
    context.user_data.pop('selected_user_unique_id', None)

    await update.message.reply_text(
        f"✅ <b>Баллы успешно добавлены!</b>\n\n"
        f"👤 Пользователь: {selected_user_name}\n"
        f"🆔 ID: #{selected_user_unique_id}\n"
        f"⭐ Добавлено: {points} баллов\n"
        f"💰 Новый баланс: {users[selected_user_id]['points']} баллов",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def admin_create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания задания"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 <b>Создание нового задания</b>\n\n"
        "Введите название задания:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_CREATE_TASK

async def admin_create_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия задания"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Создание задания отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем название задания
    context.user_data['task_name'] = text

    await update.message.reply_text(
        f"📝 <b>Название задания:</b> {text}\n\n"
        "Теперь введите количество баллов за выполнение задания:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_SET_TASK_POINTS

async def admin_set_task_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка баллов за задание и сохранение"""
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

    task_name = context.user_data.get('task_name')

    if not task_name:
        await update.message.reply_text(
            "❌ Ошибка: название задания не найдено. Начните заново.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Сохраняем задание
    tasks = load_tasks()
    task_id = generate_unique_id(tasks)

    tasks[task_id] = {
        'name': task_name,
        'points': points,
        'created_at': datetime.now().isoformat(),
        'created_by': update.effective_user.id
    }
    save_tasks(tasks)

    # Очищаем контекст
    context.user_data.pop('task_name', None)

    await update.message.reply_text(
        f"✅ <b>Задание успешно создано!</b>\n\n"
        f"📝 Задание #{task_id}\n"
        f"🎯 Название: {task_name}\n"
        f"⭐ Баллы за выполнение: {points}\n\n"
        f"Теперь пользователи могут отправлять выполнение этого задания!",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def admin_list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список заданий для администратора"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    tasks = load_tasks()

    if not tasks:
        await update.message.reply_text(
            "📭 Заданий нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    tasks_text = "📋 <b>Список заданий</b>\n\n"

    for task_id, task in tasks.items():
        tasks_text += (
            f"📝 <b>Задание #{task_id}</b>\n"
            f"🎯 Название: {task['name']}\n"
            f"⭐ Баллы: {task['points']}\n"
            f"📅 Создано: {task.get('created_at', 'Неизвестно')}\n"
            f"────────────────────\n"
        )

    await update.message.reply_text(
        tasks_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def submit_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало отправки задания"""
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы. Используйте команду /start для регистрации."
        )
        return ConversationHandler.END

    tasks = load_tasks()

    if not tasks:
        await update.message.reply_text(
            "📭 На данный момент нет доступных заданий.\n"
            "Ожидайте новых заданий от администраторов!",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    # Создаем клавиатуру с заданиями
    keyboard = []
    for task_id, task in tasks.items():
        button_text = f"📝 {task['name']} ({task['points']} баллов)"
        keyboard.append([KeyboardButton(button_text)])

    keyboard.append([KeyboardButton("🔙 Отмена")])

    await update.message.reply_text(
        "📤 <b>Отправка задания</b>\n\n"
        "Выберите задание для отправки:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return USER_SUBMIT_TASK

async def submit_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора задания и запрос доказательства"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Отправка задания отменена.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    # Извлекаем название задания из текста
    try:
        task_name = text.split(' (')[0][2:]  # Убираем эмодзи и пробел
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора задания. Попробуйте еще раз:"
        )
        return USER_SUBMIT_TASK

    tasks = load_tasks()

    # Находим задание по названию
    selected_task = None
    selected_task_id = None

    for task_id, task in tasks.items():
        if task['name'] == task_name:
            selected_task = task
            selected_task_id = task_id
            break

    if not selected_task:
        await update.message.reply_text(
            "❌ Задание не найдено. Попробуйте еще раз:"
        )
        return USER_SUBMIT_TASK

    # Сохраняем выбранное задание в контексте
    context.user_data['selected_task'] = selected_task
    context.user_data['selected_task_id'] = selected_task_id

    await update.message.reply_text(
        f"📝 <b>Вы выбрали задание:</b>\n\n"
        f"🎯 {selected_task['name']}\n"
        f"⭐ Баллы за выполнение: {selected_task['points']}\n\n"
        f"Теперь отправьте доказательство выполнения задания "
        f"(текст, фото, видео или документ):",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return USER_SUBMIT_TASK

async def handle_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка доказательства выполнения задания"""
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    selected_task = context.user_data.get('selected_task')
    selected_task_id = context.user_data.get('selected_task_id')

    if not selected_task or not selected_task_id:
        await update.message.reply_text(
            "❌ Ошибка: задание не найдено. Начните заново.",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    user_data = users[user_id]

    # Сохраняем отправку
    submissions = load_submissions()
    submission_id = generate_unique_id(submissions)

    # Определяем тип контента
    content_type = 'text'
    content = update.message.text or ''

    if update.message.photo:
        content_type = 'photo'
        content = f"Фото: {update.message.photo[-1].file_id}"
    elif update.message.video:
        content_type = 'video'
        content = f"Видео: {update.message.video.file_id}"
    elif update.message.document:
        content_type = 'document'
        content = f"Документ: {update.message.document.file_id}"

    submissions[submission_id] = {
        'user_id': user_id,
        'user_name': f"{user_data['first_name']} {user_data['surname']}",
        'user_unique_id': user_data['unique_id'],
        'task_id': selected_task_id,
        'task_name': selected_task['name'],
        'task_points': selected_task['points'],
        'content_type': content_type,
        'content': content,
        'submission_time': datetime.now().isoformat(),
        'status': 'pending',
        'reviewed_by': None,
        'reviewed_at': None
    }
    save_submissions(submissions)

    # Уведомляем администраторов
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📨 <b>Новая отправка задания!</b>\n\n"
                     f"👤 <b>Пользователь:</b> {user_data['first_name']} {user_data['surname']} (ID: #{user_data['unique_id']})\n"
                     f"📝 <b>Задание:</b> {selected_task['name']}\n"
                     f"⭐ <b>Баллы:</b> {selected_task['points']}\n"
                     f"🆔 <b>Отправка #:</b> {submission_id}\n"
                     f"🕒 <b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"Для проверки используйте панель администратора.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    await update.message.reply_text(
        f"✅ <b>Отправка успешно сохранена!</b>\n\n"
        f"📝 <b>Задание:</b> {selected_task['name']}\n"
        f"⭐ <b>Баллы за выполнение:</b> {selected_task['points']}\n"
        f"🆔 <b>Номер отправки:</b> #{submission_id}\n\n"
        f"Ожидайте проверки администратором. "
        f"Вы получите уведомление, когда отправка будет проверена.",
        parse_mode='HTML',
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

    # Очищаем контекст
    context.user_data.pop('selected_task', None)
    context.user_data.pop('selected_task_id', None)

    return ConversationHandler.END

async def admin_review_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка отправленных заданий"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    submissions = load_submissions()

    # Фильтруем только ожидающие проверки
    pending_submissions = {
        sub_id: sub for sub_id, sub in submissions.items()
        if sub['status'] == 'pending'
    }

    if not pending_submissions:
        await update.message.reply_text(
            "📭 Нет отправок, ожидающих проверки.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Создаем inline клавиатуру с отправками
    keyboard = []
    for sub_id, submission in pending_submissions.items():
        button_text = f"#{sub_id} - {submission['user_name']} - {submission['task_name']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"review_{sub_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="review_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📨 <b>Проверка отправленных заданий</b>\n\n"
        "Выберите отправку для проверки:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return ADMIN_REVIEW_SELECT

async def handle_review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов для проверки заданий"""
    query = update.callback_query
    await query.answer()

    if query.data == "review_cancel":
        await query.edit_message_text(
            "❌ Проверка отправок отменена.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    if query.data.startswith("review_"):
        submission_id = query.data.split('_')[1]
        submissions = load_submissions()

        if submission_id not in submissions:
            await query.edit_message_text(
                "❌ Отправка не найдена.",
                reply_markup=get_admin_keyboard()
            )
            return ConversationHandler.END

        submission = submissions[submission_id]

        # Показываем детали отправки
        submission_text = (
            f"📨 <b>Отправка #{submission_id}</b>\n\n"
            f"👤 <b>Пользователь:</b> {submission['user_name']} (ID: #{submission['user_unique_id']})\n"
            f"📝 <b>Задание:</b> {submission['task_name']}\n"
            f"⭐ <b>Баллы:</b> {submission['task_points']}\n"
            f"🕒 <b>Время отправки:</b> {submission['submission_time']}\n"
            f"📄 <b>Тип контента:</b> {submission['content_type']}\n\n"
        )

        if submission['content_type'] == 'text':
            submission_text += f"<b>Содержание:</b>\n{submission['content']}\n\n"
        else:
            submission_text += f"<b>Файл:</b> {submission['content']}\n\n"

        submission_text += "<b>Выберите действие:</b>"

        # Создаем клавиатуру для принятия/отклонения
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять", callback_data=f"accept_{submission_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{submission_id}")
            ],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="review_back")]
        ]

        await query.edit_message_text(
            submission_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "review_back":
        return await admin_review_submissions(update, context)

    elif query.data.startswith("accept_") or query.data.startswith("reject_"):
        action = query.data.split('_')[0]
        submission_id = query.data.split('_')[1]

        submissions = load_submissions()
        users = load_users()

        if submission_id not in submissions:
            await query.edit_message_text(
                "❌ Отправка не найдена.",
                reply_markup=get_admin_keyboard()
            )
            return ConversationHandler.END

        submission = submissions[submission_id]
        user_id = submission['user_id']

        if action == "accept":
            # Начисляем баллы
            if user_id in users:
                users[user_id]['points'] += submission['task_points']
                save_users(users)

            submissions[submission_id]['status'] = 'accepted'
            submissions[submission_id]['reviewed_by'] = query.from_user.id
            submissions[submission_id]['reviewed_at'] = datetime.now().isoformat()
            save_submissions(submissions)

            # Уведомляем пользователя
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"🎉 <b>Ваша отправка проверена!</b>\n\n"
                         f"📝 <b>Задание:</b> {submission['task_name']}\n"
                         f"✅ <b>Статус:</b> Принято\n"
                         f"⭐ <b>Начислено баллов:</b> {submission['task_points']}\n"
                         f"💰 <b>Текущий баланс:</b> {users[user_id]['points']} баллов\n"
                         f"🆔 <b>Номер отправки:</b> #{submission_id}\n\n"
                         f"Поздравляем с успешным выполнением задания! 🎊",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")

            await query.edit_message_text(
                f"✅ <b>Отправка принята!</b>\n\n"
                f"👤 Пользователь: {submission['user_name']}\n"
                f"📝 Задание: {submission['task_name']}\n"
                f"⭐ Начислено баллов: {submission['task_points']}\n"
                f"💰 Новый баланс: {users[user_id]['points']} баллов",
                parse_mode='HTML',
                reply_markup=get_admin_keyboard()
            )

        else:  # reject
            submissions[submission_id]['status'] = 'rejected'
            submissions[submission_id]['reviewed_by'] = query.from_user.id
            submissions[submission_id]['reviewed_at'] = datetime.now().isoformat()
            save_submissions(submissions)

            # Уведомляем пользователя
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"❌ <b>Ваша отправка проверена</b>\n\n"
                         f"📝 <b>Задание:</b> {submission['task_name']}\n"
                         f"❌ <b>Статус:</b> Отклонено\n"
                         f"🆔 <b>Номер отправки:</b> #{submission_id}\n\n"
                         f"Пожалуйста, проверьте требования к заданию и попробуйте снова.",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")

            await query.edit_message_text(
                f"❌ <b>Отправка отклонена!</b>\n\n"
                f"👤 Пользователь: {submission['user_name']}\n"
                f"📝 Задание: {submission['task_name']}\n"
                f"🆔 Номер отправки: #{submission_id}",
                parse_mode='HTML',
                reply_markup=get_admin_keyboard()
            )

    return ConversationHandler.END

async def admin_fix_id_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало исправления ID"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Создаем клавиатуру с пользователями
    keyboard = []
    for telegram_id, user_data in users.items():
        button_text = f"#{user_data['unique_id']} - {user_data['first_name']} {user_data['surname']}"
        keyboard.append([KeyboardButton(button_text)])

    keyboard.append([KeyboardButton("🔙 Отмена")])

    await update.message.reply_text(
        "🆔 <b>Исправление ID пользователя</b>\n\n"
        "Выберите пользователя для исправления ID:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ADMIN_FIX_ID_SELECT_USER

async def admin_fix_id_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор пользователя для исправления ID"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Исправление ID отменено.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    # Извлекаем ID пользователя из текста
    try:
        unique_id = int(text.split('#')[1].split(' ')[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Ошибка выбора пользователя. Попробуйте еще раз:"
        )
        return ADMIN_FIX_ID_SELECT_USER

    users = load_users()

    # Находим пользователя по unique_id
    selected_user = None
    selected_user_id = None

    for telegram_id, user_data in users.items():
        if user_data['unique_id'] == unique_id:
            selected_user = user_data
            selected_user_id = telegram_id
            break

    if not selected_user:
        await update.message.reply_text(
            "❌ Пользователь не найден. Попробуйте еще раз:"
        )
        return ADMIN_FIX_ID_SELECT_USER

    # Сохраняем выбранного пользователя в контексте
    context.user_data['selected_user_id'] = selected_user_id
    context.user_data['selected_user_name'] = f"{selected_user['first_name']} {selected_user['surname']}"
    context.user_data['selected_user_old_id'] = unique_id

    await update.message.reply_text(
        f"👤 <b>Выбран пользователь:</b>\n\n"
        f"🆔 Текущий ID: #{unique_id}\n"
        f"👤 Имя: {selected_user['first_name']} {selected_user['surname']}\n\n"
        f"Введите новый ID (целое число):",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_FIX_ID_SET_NEW

async def admin_fix_id_set_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка нового ID"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Исправление ID отменено.",
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

    selected_user_id = context.user_data.get('selected_user_id')
    selected_user_name = context.user_data.get('selected_user_name')
    old_id = context.user_data.get('selected_user_old_id')

    if not selected_user_id:
        await update.message.reply_text(
            "❌ Ошибка: пользователь не найден. Начните заново.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    users = load_users()

    # Проверяем, не занят ли новый ID
    for telegram_id, user_data in users.items():
        if user_data['unique_id'] == new_id and telegram_id != selected_user_id:
            await update.message.reply_text(
                f"❌ ID #{new_id} уже занят пользователем {user_data['first_name']} {user_data['surname']}. "
                f"Попробуйте другой ID:"
            )
            return ADMIN_FIX_ID_SET_NEW

    # Обновляем ID
    users[selected_user_id]['unique_id'] = new_id
    save_users(users)

    # Очищаем контекст
    context.user_data.pop('selected_user_id', None)
    context.user_data.pop('selected_user_name', None)
    context.user_data.pop('selected_user_old_id', None)

    await update.message.reply_text(
        f"✅ <b>ID успешно изменен!</b>\n\n"
        f"👤 Пользователь: {selected_user_name}\n"
        f"🆔 Старый ID: #{old_id}\n"
        f"🆔 Новый ID: #{new_id}",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def admin_reset_users_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало сброса всех пользователей"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return ConversationHandler.END

    users = load_users()

    if not users:
        await update.message.reply_text(
            "📭 Пользователей для сброса нет.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "⚠️ <b>ВНИМАНИЕ! ОПАСНАЯ ОПЕРАЦИЯ!</b>\n\n"
        "Вы собираетесь удалить ВСЕХ пользователей и ВСЕ данные.\n\n"
        "<b>Это действие:</b>\n"
        "• Удалит всех пользователей\n"
        "• Удалит все задания\n"
        "• Удалит все отправки\n"
        "• Удалит все товары и заказы\n"
        "• <b>НЕЛЬЗЯ ОТМЕНИТЬ!</b>\n\n"
        "Для подтверждения введите: <code>ПОДТВЕРЖДАЮ СБРОС</code>",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Отмена")]], resize_keyboard=True)
    )

    return ADMIN_CONFIRM_RESET

async def admin_confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение сброса всех данных"""
    text = update.message.text

    if text == "🔙 Отмена":
        await update.message.reply_text(
            "❌ Сброс данных отменен.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    if text != "ПОДТВЕРЖДАЮ СБРОС":
        await update.message.reply_text(
            "❌ Для подтверждения сброса введите точно: <code>ПОДТВЕРЖДАЮ СБРОС</code>",
            parse_mode='HTML'
        )
        return ADMIN_CONFIRM_RESET

    # Удаляем все файлы с данными
    files_to_delete = [DATA_FILE, TASKS_FILE, SUBMISSIONS_FILE, PRODUCTS_FILE, ORDERS_FILE]

    deleted_files = []
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(file_path)
        except Exception as e:
            logger.error(f"Ошибка удаления файла {file_path}: {e}")

    await update.message.reply_text(
        f"🗑️ <b>Все данные сброшены!</b>\n\n"
        f"Удаленные файлы:\n"
        f"• {DATA_FILE}\n"
        f"• {TASKS_FILE}\n"
        f"• {SUBMISSIONS_FILE}\n"
        f"• {PRODUCTS_FILE}\n"
        f"• {ORDERS_FILE}\n\n"
        f"Теперь база данных пуста. Новые пользователи могут зарегистрироваться с помощью /start",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

    return ConversationHandler.END

async def admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика системы"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return

    users = load_users()
    tasks = load_tasks()
    submissions = load_submissions()
    products = load_products()
    orders = load_orders()

    # Статистика пользователей
    total_users = len(users)
    total_points = sum(user['points'] for user in users.values())
    average_points = total_points / total_users if total_users > 0 else 0

    # Статистика заданий
    total_tasks = len(tasks)
    total_task_points = sum(task['points'] for task in tasks.values())

    # Статистика отправок
    total_submissions = len(submissions)
    pending_submissions = len([s for s in submissions.values() if s['status'] == 'pending'])
    accepted_submissions = len([s for s in submissions.values() if s['status'] == 'accepted'])
    rejected_submissions = len([s for s in submissions.values() if s['status'] == 'rejected'])

    # Статистика товаров
    total_products = len(products)
    total_products_sold = sum(product.get('sold', 0) for product in products.values())
    total_revenue = sum(product.get('sold', 0) * product['price'] for product in products.values())

    # Статистика заказов
    total_orders = len(orders)

    stats_text = (
        "📊 <b>Статистика системы</b>\n\n"
        
        "👥 <b>Пользователи:</b>\n"
        f"• Всего пользователей: {total_users}\n"
        f"• Всего баллов в системе: {total_points}\n"
        f"• Средний балл на пользователя: {average_points:.1f}\n\n"
        
        "📝 <b>Задания:</b>\n"
        f"• Всего заданий: {total_tasks}\n"
        f"• Всего возможных баллов: {total_task_points}\n\n"
        
        "📨 <b>Отправки заданий:</b>\n"
        f"• Всего отправок: {total_submissions}\n"
        f"• Ожидают проверки: {pending_submissions}\n"
        f"• Принято: {accepted_submissions}\n"
        f"• Отклонено: {rejected_submissions}\n\n"
        
        "🛍️ <b>Магазин:</b>\n"
        f"• Всего товаров: {total_products}\n"
        f"• Всего продаж: {total_products_sold}\n"
        f"• Общая выручка: {total_revenue} баллов\n\n"
        
        "📦 <b>Заказы:</b>\n"
        f"• Всего заказов: {total_orders}"
    )

    await update.message.reply_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    # Проверяем, зарегистрирован ли пользователь
    users = load_users()
    if str(user_id) not in users and text != "/start":
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
    elif text == "🔙 Главное меню":
        await update.message.reply_text(
            "🔙 Возврат в главное меню.",
            reply_markup=get_main_keyboard(user_id)
        )

    # Обработка кнопок администратора
    elif text == "👥 Список пользователей":
        await admin_list_users(update, context)
    elif text == "⭐ Добавить баллы":
        await admin_add_points_start(update, context)
    elif text == "📝 Создать задание":
        await admin_create_task_start(update, context)
    elif text == "📋 Список заданий":
        await admin_list_tasks(update, context)
    elif text == "📨 Проверка заданий":
        await admin_review_submissions(update, context)
    elif text == "🛍️ Добавить товар":
        await admin_create_product_start(update, context)
    elif text == "📦 Список товаров":
        await admin_list_products(update, context)
    elif text == "🗑️ Удалить товар":
        await admin_delete_product(update, context)
    elif text == "🆔 Исправить ID":
        await admin_fix_id_start(update, context)
    elif text == "🗑️ Сбросить пользователей":
        await admin_reset_users_start(update, context)
    elif text == "📊 Статистика":
        await admin_statistics(update, context)

    else:
        await update.message.reply_text(
            "🤔 Не понимаю вашу команду. Используйте кнопки меню.",
            reply_markup=get_main_keyboard(user_id)
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена любого действия"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard(user_id)
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления {update}: {context.error}")

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте еще раз."
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

def main():
    """Основная функция запуска бота"""
    # Создаем Application
    application = Application.builder().token(TOKEN).build()

    # Обработчик регистрации
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_FIRST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_first_name)
            ],
            WAITING_FOR_SURNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_surname)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик добавления баллов
    add_points_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⭐ Добавить баллы$"), admin_add_points_start)],
        states={
            ADMIN_SELECT_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_select_user)
            ],
            ADMIN_ADD_POINTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_points)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик создания задания
    create_task_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Создать задание$"), admin_create_task_start)],
        states={
            ADMIN_CREATE_TASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_task)
            ],
            ADMIN_SET_TASK_POINTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_task_points)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик отправки задания
    submit_task_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📤 Отправить задание$"), submit_task_start)],
        states={
            USER_SUBMIT_TASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, submit_task),
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.DOCUMENT, handle_submission)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик исправления ID
    fix_id_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🆔 Исправить ID$"), admin_fix_id_start)],
        states={
            ADMIN_FIX_ID_SELECT_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_fix_id_select_user)
            ],
            ADMIN_FIX_ID_SET_NEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_fix_id_set_new)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик сброса пользователей
    reset_users_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑️ Сбросить пользователей$"), admin_reset_users_start)],
        states={
            ADMIN_CONFIRM_RESET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_confirm_reset)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик проверки заданий
    review_submissions_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📨 Проверка заданий$"), admin_review_submissions)],
        states={
            ADMIN_REVIEW_SELECT: [
                CallbackQueryHandler(handle_review_callback, pattern="^review_")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик создания товара
    create_product_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛍️ Добавить товар$"), admin_create_product_start)],
        states={
            ADMIN_CREATE_PRODUCT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_product_name)
            ],
            ADMIN_CREATE_PRODUCT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_product_description)
            ],
            ADMIN_CREATE_PRODUCT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_create_product_price)
            ],
            ADMIN_SET_PRODUCT_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_product_quantity)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Обработчик покупки товара
    buy_product_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒 Купить товар #"), buy_product)],
        states={
            USER_BUY_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, buy_product)
            ],
            USER_CONFIRM_PURCHASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_purchase)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавляем обработчики
    application.add_handler(registration_handler)
    application.add_handler(add_points_handler)
    application.add_handler(create_task_handler)
    application.add_handler(submit_task_handler)
    application.add_handler(fix_id_handler)
    application.add_handler(reset_users_handler)
    application.add_handler(review_submissions_handler)
    application.add_handler(create_product_handler)
    application.add_handler(buy_product_handler)

    # Обработчик callback'ов для удаления товара
    application.add_handler(CallbackQueryHandler(handle_delete_product_callback, pattern="^delete_"))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    if webhook_url:
        # Используем вебхук для Railway
        logger.info(f"Starting bot in webhook mode on port {port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"{webhook_url}/{TOKEN}"
        )
    else:
        # Используем polling для локальной разработки
        logger.info("Starting bot in polling mode")
        application.run_polling()

if __name__ == '__main__':
    main()

