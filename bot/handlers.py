# bot/handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from .database import Database
from .selenium_parser import OzonSeleniumParser
from datetime import datetime

db = Database()
parser = OzonSeleniumParser(headless=True)  # Используем исправленный парсер


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    db.add_user(user.id, user.username)

    welcome_text = f"""Привет, {user.first_name}! 👋

Я помогу отслеживать изменения цен на товары Ozon.

Доступные команды:
/add - Добавить товар для отслеживания
/list - Показать мои товары
/remove - Удалить товар из отслеживания
/help - Помощь

Пример: /add https://www.ozon.ru/product/12345678/
"""

    await update.message.reply_text(welcome_text)


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление товара для отслеживания"""
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите ссылку на товар Ozon.\n"
            "Пример: /add https://www.ozon.ru/product/12345678/"
        )
        return

    url = context.args[0]

    # Проверяем, что это ссылка Ozon
    if 'ozon.ru' not in url and 'ozon.com' not in url:
        await update.message.reply_text("Пожалуйста, укажите ссылку на товар Ozon.")
        return

    await update.message.reply_text("⏳ Ищу товар...")

    try:
        # Получаем информацию о товаре
        product_info = parser.get_product_info(url)

        if not product_info:
            await update.message.reply_text(
                "❌ Не удалось получить информацию о товаре.\n"
                "Возможные причины:\n"
                "1. Товар не существует\n"
                "2. Проблема с соединением\n"
                "3. Ozon временно блокирует запросы"
            )
            return

        if not product_info.get('price'):
            await update.message.reply_text(
                f"✅ Товар найден, но цену определить не удалось!\n\n"
                f"📦 {product_info.get('name', 'Неизвестный товар')}\n\n"
                f"Товар добавлен, цена будет определена при следующей проверке."
            )
            price = 0
        else:
            price = product_info['price']

        # Сохраняем товар в базу
        product = db.add_product(
            url=url,
            product_id=product_info.get('product_id', 'unknown'),
            name=product_info.get('name', 'Неизвестный товар'),
            price=price
        )

        # Связываем товар с пользователем
        user = db.add_user(update.effective_user.id, update.effective_user.username)
        db.add_user_product(user.id, product.id)

        if price > 0:
            availability = "✅ В наличии" if product_info.get('available', True) else "❌ Нет в наличии"

            await update.message.reply_text(
                f"✅ Товар добавлен для отслеживания!\n\n"
                f"📦 {product_info['name']}\n"
                f"💰 Текущая цена: {price}₽\n"
                f"📊 {availability}\n\n"
                f"Я буду уведомлять вас об изменении цены."
            )
        else:
            await update.message.reply_text(
                f"✅ Товар добавлен для отслеживания!\n\n"
                f"📦 {product_info['name']}\n"
                f"💰 Цена будет определена при следующей проверке.\n\n"
                f"Я буду уведомлять вас об изменении цены."
            )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Ошибка при обработке товара: {str(e)[:100]}\n"
            f"Попробуйте позже или используйте другую ссылку."
        )
        print(f"Ошибка в add_product: {e}")


async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список отслеживаемых товаров"""
    user = db.add_user(update.effective_user.id, update.effective_user.username)
    products = db.get_user_products(user.id)

    if not products:
        await update.message.reply_text("У вас нет отслеживаемых товаров.\nДобавьте товар командой /add")
        return

    message = "📋 Ваши отслеживаемые товары:\n\n"

    for i, product in enumerate(products, 1):
        change = ""
        if product.previous_price and product.current_price:
            change_percent = ((product.current_price - product.previous_price) / product.previous_price) * 100
            if abs(change_percent) > 0.1:
                change = f" ({'📈 +' if change_percent > 0 else '📉 '}{change_percent:.1f}%)"

        message += f"{i}. {product.name}\n"
        message += f"   Цена: {product.current_price}₽{change}\n"
        if product.last_check:
            message += f"   Последняя проверка: {product.last_check.strftime('%d.%m.%Y %H:%M')}\n\n"
        else:
            message += f"   Еще не проверялось\n\n"

    message += "❌ Для удаления товара используйте /remove <номер>"
    await update.message.reply_text(message)


async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление товара из отслеживания"""
    user = db.add_user(update.effective_user.id, update.effective_user.username)
    products = db.get_user_products(user.id)

    if not products:
        await update.message.reply_text("У вас нет отслеживаемых товаров для удаления.")
        return

    # Если номер товара не указан - показываем список для удаления
    if not context.args:
        message = "❓ Укажите номер товара для удаления:\n\n"
        for i, product in enumerate(products, 1):
            message += f"{i}. {product.name}\n"

        message += "\nПример: /remove 1"
        await update.message.reply_text(message)
        return

    try:
        # Получаем номер товара из аргументов
        product_num = int(context.args[0])

        # Проверяем, что номер в допустимом диапазоне
        if product_num < 1 or product_num > len(products):
            await update.message.reply_text(
                f"Пожалуйста, укажите номер от 1 до {len(products)}"
            )
            return

        # Получаем товар для удаления
        product_to_remove = products[product_num - 1]

        # Находим связь пользователя с товаром
        from .database import UserProduct
        user_product = db.session.query(UserProduct).filter_by(
            user_id=user.id,
            product_id=product_to_remove.id
        ).first()

        if user_product:
            # Удаляем связь
            db.session.delete(user_product)
            db.session.commit()

            await update.message.reply_text(
                f"✅ Товар удалён из отслеживания:\n"
                f"📦 {product_to_remove.name}"
            )
        else:
            await update.message.reply_text("❌ Не удалось найти товар для удаления.")

    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите номер товара (например: /remove 1)")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при удалении: {str(e)[:50]}")
        print(f"Ошибка в remove_product: {e}")

"""
async def check_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Ручная проверка и отправка оповещений об изменении цен
    user = db.add_user(update.effective_user.id, update.effective_user.username)

    await update.message.reply_text("⏳ Запускаю проверку цен для оповещений...")

    try:
        # Получаем все товары пользователя
        user_products = db.get_user_products(user.id)

        if not user_products:
            await update.message.reply_text("У вас нет отслеживаемых товаров.")
            return

        notifications_sent = 0
        changed_products = []

        for product in user_products:
            # Получаем актуальную цену через парсер
            try:
                product_info = parser.get_product_info(product.url)

                if product_info and product_info.get('price'):
                    new_price = product_info['price']
                    old_price = product.current_price

                    # Проверяем изменение цены (более чем на 1%)
                    if old_price > 0 and abs(new_price - old_price) / old_price * 100 >= 1:
                        # Обновляем цену в базе
                        db.update_product_price(product.id, new_price)

                        # Формируем сообщение
                        change_percent = ((new_price - old_price) / old_price) * 100
                        change_icon = "📈" if change_percent > 0 else "📉"

                        message = (
                            f"{change_icon} *Изменилась цена товара!*\n\n"
                            f"📦 *{product.name}*\n"
                            f"💰 *Старая цена:* {old_price}₽\n"
                            f"💰 *Новая цена:* {new_price}₽\n"
                            f"📊 *Изменение:* {change_percent:+.1f}%\n\n"
                            f"[Ссылка на товар]({product.url})"
                        )

                        # Отправляем уведомление
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=message,
                            parse_mode='Markdown'
                        )

                        notifications_sent += 1
                        changed_products.append(product.name)

                        # Небольшая задержка, чтобы не блокировать
                        import asyncio
                        await asyncio.sleep(0.5)

            except Exception as e:
                print(f"Ошибка при проверке товара {product.name}: {e}")
                continue

        # Формируем отчет
        if notifications_sent > 0:
            report = f"✅ Проверка завершена!\n\nОтправлено оповещений: {notifications_sent}\n\n"
            report += "Изменения по товарам:\n"
            for i, prod_name in enumerate(changed_products, 1):
                report += f"{i}. {prod_name}\n"
        else:
            report = "✅ Проверка завершена!\n\nИзменений цен не обнаружено."

        await update.message.reply_text(report)

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке оповещений: {str(e)[:100]}"
        print(f"Ошибка в check_notifications: {e}")
        await update.message.reply_text(error_msg)
"""

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка"""
    help_text = """📚 Помощь по использованию бота:

Команды:
/start - Начать работу с ботом
/add <ссылка> - Добавить товар для отслеживания
/list - Показать все отслеживаемые товары
/remove - Удалить товар из отслеживания
/help - Эта справка
*Тестовые команды (для отладки):*
/test_alert - Отправить тестовое оповещение
/test_simulate - Имитация изменения цены

Пример добавления товара:
/add https://www.ozon.ru/product/123456789/
Пример удаления товара:
/remove 1

Бот проверяет цены каждый час и присылает уведомления при изменении цены более чем на 5%.
/check - Проверка изменения цен "вручную"
"""

    await update.message.reply_text(help_text)


async def test_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая тестовая команда для проверки оповещений"""
    try:
        user_id = update.effective_user.id

        # Простое тестовое сообщение
        test_message = (
            f"🔔 *ТЕСТОВОЕ ОПОВЕЩЕНИЕ*\n\n"
            f"📦 *Тестовый товар: Блок питания*\n"
            f"💰 *Старая цена:* 850₽\n"
            f"💰 *Новая цена:* 1063₽\n"
            f"📊 *Изменение:* +25.0%\n\n"
            f"✅ *Это тестовое сообщение*\n"
            f"📅 *Время:* {datetime.now().strftime('%H:%M:%S')}"
        )

        # Отправляем тестовое сообщение
        await update.message.reply_text(test_message, parse_mode='Markdown')

        # Также отправляем через context.bot для проверки
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Второе тестовое сообщение через context.bot",
                parse_mode='Markdown'
            )
        except Exception as bot_err:
            await update.message.reply_text(f"⚠️ Ошибка context.bot: {str(bot_err)[:50]}")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")


async def simulate_price_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Симулировать изменение цены для тестирования оповещений"""
    try:
        user_id = update.effective_user.id
        await update.message.reply_text("🔧 Запускаю симуляцию изменения цены...")

        user = db.add_user(user_id, update.effective_user.username)
        products = db.get_user_products(user.id)

        if not products:
            await update.message.reply_text("У вас нет товаров для тестирования.")
            return

        # Берем первый товар
        product = products[0]

        await update.message.reply_text(f"📦 Выбран товар: {product.name}")

        # Получаем текущие значения ИЗ БАЗЫ
        original_previous = product.previous_price
        original_current = product.current_price

        await update.message.reply_text(
            f"📊 *Исходное состояние базы:*\n"
            f"• previous_price: {original_previous}₽\n"
            f"• current_price: {original_current}₽"
        )

        # Если current_price не установлен, используем 1000 для теста
        current_price = original_current or 1000

        if current_price <= 0:
            current_price = 1000

        # Искусственная старая цена (на 20% ниже)
        test_old_price = round(current_price * 0.8, 2)

        await update.message.reply_text(
            f"💰 *Тестовые значения:*\n"
            f"• Искусственная previous_price: {test_old_price}₽\n"
            f"• current_price: {current_price}₽\n"
            f"• Имитация изменения: +25.0%"
        )

        # ВАЖНО: Сохраняем точные копии значений
        saved_previous = float(original_previous) if original_previous else None
        saved_current = float(original_current) if original_current else None

        # Устанавливаем тестовые значения
        product.previous_price = test_old_price
        product.current_price = current_price
        db.session.commit()

        await update.message.reply_text("✅ Тестовые значения установлены в базу")

        # Формируем тестовое сообщение
        change_percent = round(((current_price - test_old_price) / test_old_price) * 100, 1)
        alert_message = (
            f"🧪 *ТЕСТОВОЕ ОПОВЕЩЕНИЕ:*\n\n"
            f"📦 *{product.name}*\n"
            f"💰 *Была:* {test_old_price}₽\n"
            f"💰 *Стала:* {current_price}₽\n"
            f"📊 *Изменение:* {change_percent:+.1f}%\n\n"
            f"🔗 *Ссылка:* {product.url}\n\n"
            f"⚠️ *Это тестовое оповещение для проверки системы*"
        )

        # Отправляем тестовое оповещение
        await context.bot.send_message(
            chat_id=user_id,
            text=alert_message,
            parse_mode='Markdown'
        )

        await update.message.reply_text("✅ Тестовое оповещение отправлено")

        # ВАЖНО: ПОЛНОЕ ВОССТАНОВЛЕНИЕ исходных значений
        product.previous_price = saved_previous
        product.current_price = saved_current
        db.session.commit()

        await update.message.reply_text(
            f"🔄 *Восстановлено исходное состояние:*\n\n"
            f"📦 Товар: {product.name}\n"
            f"💰 previous_price: {saved_previous}₽\n"
            f"💰 current_price: {saved_current}₽\n\n"
            f"✅ База данных полностью восстановлена"
        )

    except Exception as e:
        # Даже при ошибке пытаемся восстановить базу
        try:
            if 'product' in locals() and 'saved_previous' in locals():
                product.previous_price = saved_previous
                product.current_price = saved_current
                db.session.commit()
        except:
            pass

        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")
        print(f"Ошибка в simulate_price_change: {e}")


def get_product_by_name(self, name):
    """Найти товар по имени"""
    return self.session.query(Product).filter(Product.name.like(f"%{name}%")).first()


def create_test_price_change(self, product_id):
    """Создать искусственное изменение цены для теста"""
    product = self.session.query(Product).filter_by(id=product_id).first()
    if product and product.current_price > 0:
        # Устанавливаем предыдущую цену на 10% ниже
        product.previous_price = product.current_price * 0.9
        self.session.commit()
        return True
    return False


async def create_test_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать тестовое изменение цены в базе"""
    user = db.add_user(update.effective_user.id, update.effective_user.username)
    products = db.get_user_products(user.id)

    if not products:
        await update.message.reply_text("У вас нет товаров.")
        return

    product = products[0]

    # Сохраняем текущие значения
    real_current = product.current_price or 1000
    real_previous = product.previous_price or real_current

    # Создаем искусственное изменение
    product.previous_price = real_current * 0.8  # -20%
    db.session.commit()

    await update.message.reply_text(
        f"✅ Создано тестовое изменение!\n\n"
        f"📦 Товар: {product.name}\n"
        f"💰 Было: {product.previous_price:.0f}₽\n"
        f"💰 Сейчас: {real_current}₽\n"
        f"📊 Изменение: +{((real_current - product.previous_price) / product.previous_price * 100):.1f}%\n\n"
        f"Теперь запустите /check для проверки оповещений"
    )


async def check_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручная проверка и отправка оповещений об изменении цен"""
    user = db.add_user(update.effective_user.id, update.effective_user.username)

    await update.message.reply_text("⏳ Запускаю проверку цен для оповещений...")

    try:
        user_products = db.get_user_products(user.id)

        if not user_products:
            await update.message.reply_text("У вас нет отслеживаемых товаров.")
            return

        notifications_sent = 0
        debug_info = []
        changed_products = []

        for product in user_products:
            try:
                # 1. Получаем актуальную цену с Ozon
                await update.message.reply_text(f"🔍 Проверяю: {product.name[:30]}...")

                product_info = parser.get_product_info(product.url)

                if not product_info or product_info.get('price') is None:
                    debug_info.append(f"{product.name[:20]}: ❌ Не удалось получить цену")
                    continue

                new_price = product_info['price']
                old_price = product.previous_price

                # 2. Отладочная информация
                debug_msg = f"{product.name[:20]}: "
                debug_msg += f"previous={old_price}₽, "
                debug_msg += f"ozon={new_price}₽"

                # 3. Проверяем изменение цены
                if old_price is None or old_price == 0:
                    # Первая проверка
                    debug_msg += " (первая проверка)"
                    db.update_product_price(product.id, new_price)
                else:
                    # Рассчитываем процент изменения
                    change_percent = ((new_price - old_price) / old_price) * 100
                    debug_msg += f", изменение={change_percent:+.1f}%"

                    # 4. Если изменение больше 1% - отправляем оповещение
                    if abs(change_percent) >= 1.0:
                        # Формируем сообщение
                        change_icon = "📈" if change_percent > 0 else "📉"
                        message = (
                            f"{change_icon} *Изменилась цена товара!*\n\n"
                            f"📦 *{product.name}*\n"
                            f"💰 *Была:* {old_price}₽\n"
                            f"💰 *Стала:* {new_price}₽\n"
                            f"📊 *Изменение:* {change_percent:+.1f}%\n\n"
                            f"[Ссылка на товар]({product.url})"
                        )

                        # Отправляем оповещение
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=message,
                            parse_mode='Markdown'
                        )

                        # Обновляем цену в базе
                        db.update_product_price(product.id, new_price)

                        notifications_sent += 1
                        changed_products.append(f"{product.name[:20]}: {old_price}₽ → {new_price}₽")

                        debug_msg += " ✅ ОПОВЕЩЕНИЕ ОТПРАВЛЕНО"
                    else:
                        # Незначительное изменение, просто обновляем
                        db.update_product_price(product.id, new_price)
                        debug_msg += " (изменение < 1%)"

                debug_info.append(debug_msg)

                # Задержка между запросами
                import asyncio
                await asyncio.sleep(2)

            except Exception as e:
                debug_info.append(f"{product.name[:20]}: ⚠️ Ошибка: {str(e)[:30]}")
                print(f"Ошибка при проверке {product.name}: {e}")
                continue

        # 5. Формируем отчет
        report = f"✅ *Проверка завершена!*\n\n"
        report += f"Проверено товаров: {len(user_products)}\n"
        report += f"Отправлено оповещений: {notifications_sent}\n\n"

        if notifications_sent > 0:
            report += "*Изменения цен:*\n"
            for item in changed_products:
                report += f"• {item}\n"
            report += "\n"

        # Добавляем детальную информацию (первые 5 товаров)
        if debug_info:
            report += "*Детали проверки:*\n"
            for i, info in enumerate(debug_info[:5], 1):
                report += f"{i}. {info}\n"

        await update.message.reply_text(report, parse_mode='Markdown')

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке оповещений: {str(e)[:100]}"
        print(f"Ошибка в check_notifications: {e}")
        await update.message.reply_text(error_msg)