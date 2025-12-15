# bot/main.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import asyncio

from .config import Config
from .handlers import (start,
                       add_product,
                       list_products,
                       remove_product,
                       help_command,
                       check_notifications,
                       simulate_price_change,
                       test_alert,
                       simulate_price_change,
                       create_test_change)
from .database import Database
from .selenium_parser import OzonSeleniumParser

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class PriceTrackerBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.parser = OzonSeleniumParser(headless=True)

    async def check_prices(self, application):
        """Проверка цен всех отслеживаемых товаров"""
        logger.info("Начинаю проверку цен...")

        products = self.db.get_all_tracked_products()

        for product in products:
            try:
                # Получаем актуальную информацию о товаре
                product_info = self.parser.get_product_info(product.url)

                if product_info and product_info.get('price'):
                    new_price = product_info['price']
                    old_price = product.current_price

                    # Проверяем изменение цены
                    if old_price and new_price != old_price:
                        change_percent = ((new_price - old_price) / old_price) * 100

                        # Если изменение больше порога - отправляем уведомления
                        if abs(change_percent) >= self.config.PRICE_CHANGE_THRESHOLD:
                            # Находим пользователей, которые отслеживают этот товар
                            from .database import UserProduct

                            user_products = self.db.session.query(UserProduct).filter_by(
                                product_id=product.id
                            ).all()

                            for user_product in user_products:
                                # Получаем пользователя
                                from .database import User
                                user = self.db.session.query(User).filter_by(id=user_product.user_id).first()

                                if user:
                                    message = (
                                        f"📢 Изменение цены!\n\n"
                                        f"📦 {product.name}\n"
                                        f"Старая цена: {old_price}₽\n"
                                        f"Новая цена: {new_price}₽\n"
                                        f"Изменение: {'📈 +' if change_percent > 0 else '📉 '}{change_percent:.1f}%\n\n"
                                        f"{product.url}"
                                    )

                                    try:
                                        await application.bot.send_message(
                                            chat_id=user.telegram_id,
                                            text=message
                                        )
                                        logger.info(f"Отправлено уведомление пользователю {user.telegram_id}")
                                    except Exception as e:
                                        logger.error(f"Ошибка отправки сообщения: {e}")

                    # Обновляем цену в базе
                    product.previous_price = product.current_price
                    product.current_price = new_price
                    product.last_check = datetime.utcnow()
                    self.db.session.commit()

                    await asyncio.sleep(2)  # Задержка между запросами

            except Exception as e:
                logger.error(f"Ошибка при проверке товара {product.id}: {e}")

        logger.info("Проверка цен завершена")

    async def setup_scheduler(self, application):
        """Настройка планировщика"""
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            self.check_prices,
            'interval',
            seconds=self.config.CHECK_INTERVAL,
            args=[application]
        )
        scheduler.start()
        logger.info("Планировщик запущен")

    async def error_handler(self, update: Update, context):
        """Обработчик ошибок"""
        logger.error(f"Ошибка при обработке сообщения: {context.error}")

    async def unknown_command(self, update: Update, context):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "Неизвестная команда. Используйте /help для списка команд."
        )

    def run(self):
        """Запуск бота"""
        # Создаем приложение
        application = Application.builder().token(self.config.TELEGRAM_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("add", add_product))
        application.add_handler(CommandHandler("list", list_products))
        application.add_handler(CommandHandler("remove", remove_product))
        application.add_handler(CommandHandler("check", check_notifications))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test_simulate", simulate_price_change))
        application.add_handler(CommandHandler("test_alert", test_alert))
        application.add_handler(CommandHandler("test_simulate", simulate_price_change))
        application.add_handler(CommandHandler("create_test", create_test_change))
        application.add_handler(CommandHandler("check", check_notifications))

        # Обработчик неизвестных команд
        application.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))

        # Обработчик ошибок
        application.add_error_handler(self.error_handler)

        # Настраиваем планировщик
        application.job_queue.run_once(
            lambda context: asyncio.create_task(self.setup_scheduler(application)),
            when=1
        )

        # Запускаем бота
        logger.info("Бот запускается...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)