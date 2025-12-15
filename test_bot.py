import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context):
    """Простой тестовый обработчик"""
    await update.message.reply_text("Тест: Бот работает!")


async def main():
    """Тестовый запуск"""
    # Вставьте ваш токен сюда напрямую для теста
    TOKEN = "7377182645:AAHwwhvA_swdNYiNgKHczYvo15eolV__73w"

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Тестовый бот запускается...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("Бот запущен! Отправьте /start в Telegram")

    # Ждем 60 секунд для теста
    await asyncio.sleep(60)

    await app.updater.stop()
    await app.stop()
    await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())