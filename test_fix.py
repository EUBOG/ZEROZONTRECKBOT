import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.selenium_parser import OzonSeleniumParser

print("🔧 Тест исправления Selenium парсера...")
try:
    # Создаём парсер, но НЕ запускаем парсинг
    parser = OzonSeleniumParser(headless=False)  # headless=False чтобы видеть браузер
    print("✅ Объект парсера создан")

    # Пробуем запустить драйвер
    parser.setup_driver()
    print("✅ Драйвер запущен успешно!")

    # Если дошли сюда, делаем простой запрос для проверки
    parser.driver.get("https://ya.ru")
    print(f"✅ Страница загружена. Заголовок: {parser.driver.title}")

    input("\n⏸️  Нажмите Enter для закрытия браузера...")
    parser.close_driver()

except Exception as e:
    print(f"\n❌ ОШИБКА: {type(e).__name__}: {e}")