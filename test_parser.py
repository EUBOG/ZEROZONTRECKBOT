import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.ozon_parser import OzonParser


def test_parser():
    parser = OzonParser()

    # Тестовые ссылки (используйте реальные из вашего браузера)
    test_urls = [
        "https://ozon.ru/t/Riz4dq5",
        "https://www.ozon.ru/product/1897356166/",
        "https://www.ozon.ru/product/smartfon-apple-iphone-15-128-gb-chernyy-1171349177/",
        # Добавьте свои ссылки сюда
    ]

    print("🔍 Начинаем тестирование парсера Ozon")
    print("=" * 50)

    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. Тестируем URL: {url}")
        print("-" * 30)

        try:
            result = parser.get_product_info(url)

            if result:
                print(f"✅ УСПЕХ!")
                print(f"   ID товара: {result.get('product_id', 'N/A')}")
                print(f"   Название: {result.get('name', 'N/A')}")
                print(f"   Цена: {result.get('price', 'N/A')}")
                print(f"   URL: {result.get('url', 'N/A')}")
            else:
                print("❌ НЕ УДАЛОСЬ ПОЛУЧИТЬ ДАННЫЕ")

        except Exception as e:
            print(f"⚠️ ИСКЛЮЧЕНИЕ: {type(e).__name__}: {e}")

    print("\n" + "=" * 50)
    print("Тестирование завершено")


if __name__ == "__main__":
    test_parser()