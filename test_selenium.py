# test_selenium.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.selenium_parser import OzonSeleniumParser
import time


def test_selenium_parser():
    """Тестирование Selenium парсера"""
    print("🚀 Запуск Selenium парсера Ozon")
    print("=" * 60)

    # Создаём парсер с отображением окна браузера (для отладки)
    parser = OzonSeleniumParser(headless=False)  # False - видим окно браузера

    try:
        # Тестовые ссылки
        test_urls = [
            "https://www.ozon.ru/product/1969863705/",
            "https://www.ozon.ru/product/blok-pitaniya-dlya-svetodiodnoy-lenty-24v-100-vt-ip40-1633807435/",
            "https://ozon.ru/t/Riz4dq5",
        ]

        for i, url in enumerate(test_urls, 1):
            print(f"\n{'=' * 40}")
            print(f"ТЕСТ {i}: {url}")
            print('=' * 40)

            start_time = time.time()

            result = parser.get_product_info(url)

            elapsed = time.time() - start_time
            print(f"⏱️ Время выполнения: {elapsed:.2f} секунд")

            if result:
                print("\n✅ РЕЗУЛЬТАТ:")
                print(f"   ID: {result.get('product_id')}")
                print(f"   Название: {result.get('name')}")
                print(f"   Цена: {result.get('price')}")
                print(f"   В наличии: {result.get('available', True)}")
                print(f"   URL: {result.get('url')}")

                # Сохраняем скриншот для отладки
                parser.save_screenshot(f"test_{i}_screenshot.png")
            else:
                print("\n❌ НЕ УДАЛОСЬ ПОЛУЧИТЬ ДАННЫЕ")

            # Пауза между запросами
            if i < len(test_urls):
                print(f"\n⏳ Пауза 3 секунды...")
                time.sleep(3)

    finally:
        # Всегда закрываем драйвер
        parser.close_driver()

    print("\n" + "=" * 60)
    print("Тестирование завершено")


if __name__ == "__main__":
    test_selenium_parser()