import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.selenium_parser import OzonSeleniumParser

print("🔧 Запуск диагностики парсера...")

try:
    # Создаём парсер с видимым браузером
    parser = OzonSeleniumParser(headless=False)
    parser.setup_driver()

    # Открываем тестовую страницу
    test_url = "https://www.ozon.ru/product/1969863705/"
    parser.driver.get(test_url)

    # 1. Проверяем, вызывается ли _extract_product_data
    print("\n1. Вызываю _extract_product_data()...")
    product_data = parser._extract_product_data()
    print(f"   Результат _extract_product_data: {product_data}")

    # 2. Если данные есть, но без цены, проверяем вызов _extract_price напрямую
    if product_data and product_data.get('price') is None:
        print("\n2. Пробую вызвать _extract_price() напрямую...")
        price = parser._extract_price()
        print(f"   Результат _extract_price: {price}")

    # 3. Проверяем атрибуты класса
    print("\n3. Проверяю методы класса...")
    print(f"   _extract_price in dir(parser): {'_extract_price' in dir(parser)}")
    print(f"   _extract_product_data in dir(parser): {'_extract_product_data' in dir(parser)}")

    input("\n⏸️ Нажмите Enter для закрытия браузера...")

except Exception as e:
    print(f"\n❌ ОШИБКА: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()

finally:
    if 'parser' in locals() and parser.driver:
        parser.driver.quit()
        print("\n✅ Браузер закрыт")