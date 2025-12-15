import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Конфигурация
YANDEX_BROWSER_PATH = r'C:\Users\79093\AppData\Local\Yandex\YandexBrowser\Application\browser.exe'
YANDEX_DRIVER_PATH = r'D:\ZERO\2025 12 15 OZON_BOT\Драйвер\yandexdriver.exe'

print("🔧 Тестируем YandexDriver с Яндекс.Браузером")
print(f"Браузер: {YANDEX_BROWSER_PATH}")
print(f"Драйвер: {YANDEX_DRIVER_PATH}")

# Настройки
options = Options()
options.binary_location = YANDEX_BROWSER_PATH
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--window-size=1400,900')

# Без headless для первой проверки
# options.add_argument('--headless')

# Запуск
try:
    service = Service(executable_path=YANDEX_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    print("\n✅ Драйвер успешно создан!")

    # Тест 1: Простая страница
    print("\n1. Открываем Яндекс...")
    driver.get("https://ya.ru")
    time.sleep(2)
    print(f"   Заголовок: {driver.title}")

    # Тест 2: Ozon
    print("\n2. Открываем Ozon...")
    driver.get("https://www.ozon.ru")
    time.sleep(3)
    print(f"   Заголовок: {driver.title}")

    # Тест 3: Конкретный товар
    print("\n3. Тестируем товар...")
    driver.get("https://www.ozon.ru/product/1897356166/")
    time.sleep(4)

    # Пробуем найти элементы
    try:
        title = driver.find_element("tag name", "h1")
        print(f"   Найден заголовок: {title.text[:60]}...")
    except:
        print("   Не найден заголовок h1")

    # Сохраняем скриншот
    driver.save_screenshot("test_yandex_ozon.png")
    print("   Скриншот сохранён: test_yandex_ozon.png")

    # Показать User Agent
    user_agent = driver.execute_script("return navigator.userAgent")
    print(f"\n📱 User Agent: {user_agent[:80]}...")

    input("\nНажмите Enter для закрытия браузера...")

except Exception as e:
    print(f"\n❌ ОШИБКА: {type(e).__name__}: {str(e)[:200]}")

finally:
    if 'driver' in locals():
        driver.quit()
        print("\n✅ Браузер закрыт")