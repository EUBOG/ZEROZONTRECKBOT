import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re

# Конфигурация
YANDEX_BROWSER_PATH = r'C:\Users\79093\AppData\Local\Yandex\YandexBrowser\Application\browser.exe'
YANDEX_DRIVER_PATH = r'D:\ZERO\2025 12 15 OZON_BOT\Драйвер\yandexdriver.exe'

print("🔧 Расширенный тест парсинга Ozon")
print("=" * 60)

# Настройки с улучшенной маскировкой
options = Options()
options.binary_location = YANDEX_BROWSER_PATH

# Отключите headless для отладки, чтобы видеть что происходит
# options.add_argument('--headless')  # ЗАКОММЕНТИРУЙТЕ ЭТУ СТРОКУ НА ВРЕМЯ ОТЛАДКИ

# Настройки для обхода защиты
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--window-size=1920,1080')
options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')

# Запуск
try:
    service = Service(executable_path=YANDEX_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # Маскировка
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    print("✅ Драйвер создан. Открываю Ozon...")

    # Тестовый товар
    test_url = "https://www.ozon.ru/product/1969863705/"
    driver.get(test_url)

    print(f"\n📄 Загружаю страницу: {test_url}")

    # Ждём полной загрузки
    time.sleep(5)  # Увеличьте время ожидания если нужно

    # Сохраняем скриншот
    driver.save_screenshot("ozon_debug.png")
    print("📸 Скриншот сохранён: ozon_debug.png")

    # Сохраняем исходный код страницы для анализа
    with open("ozon_page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("📝 Исходный код страницы сохранён: ozon_page_source.html")

    print("\n🔍 Ищу элементы на странице...")
    print("-" * 40)

    # Попробуем найти разные элементы
    test_selectors = [
        ("h1", "Заголовок h1"),
        ("[data-widget='webProductHeading']", "Виджет заголовка"),
        (".product-page__title", "Класс заголовка"),
        ("[data-widget='webPrice']", "Виджет цены"),
        ("[itemprop='name']", "Микроразметка названия"),
        ("[itemprop='price']", "Микроразметка цены"),
    ]

    found_elements = []
    for selector, description in test_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                text = elements[0].text.strip()[:100]
                found_elements.append((selector, description, text))
                print(f"✅ Найдено: {description} ('{selector}'): {text}")
            else:
                print(f"❌ Не найдено: {description} ('{selector}')")
        except Exception as e:
            print(f"⚠️ Ошибка при поиске {description}: {e}")

    print("\n📊 Найдено элементов:", len(found_elements))

    if found_elements:
        print("\n🎯 Результаты поиска:")
        for selector, desc, text in found_elements:
            print(f"  {desc}: {text}")

    # Показываем текущий URL (может быть редирект)
    print(f"\n🌐 Текущий URL: {driver.current_url}")

    # Показываем размер страницы
    print(f"📏 Размер страницы: {len(driver.page_source)} символов")

    input("\n⏸️ Нажмите Enter для закрытия браузера...")

except Exception as e:
    print(f"\n❌ ОШИБКА: {type(e).__name__}: {str(e)[:200]}")
    import traceback

    traceback.print_exc()

finally:
    if 'driver' in locals():
        driver.quit()
        print("\n✅ Браузер закрыт")