# bot/selenium_parser.py
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class OzonSeleniumParser:
    def __init__(self, headless=True):
        """
        Инициализация Selenium парсера
        :param headless: Запуск без графического интерфейса (True/False)
        """
        self.headless = headless
        self.driver = None
        self.timeout = 20  # Таймаут ожидания элементов

    def setup_driver(self):
        """Настройка и запуск Яндекс.Браузера через YandexDriver"""
        # 1. Создаём объект опций Chrome. Убедитесь, что переменная называется chrome_options
        chrome_options = Options()  # <-- Вот здесь создаётся переменная!

        # 2. Указываем путь к Яндекс.Браузеру
        chrome_options.binary_location = r'C:\Users\79093\AppData\Local\Yandex\YandexBrowser\Application\browser.exe'

        if self.headless:
            chrome_options.add_argument('--headless')

        # 3. Настройки для обхода защиты
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 4. Дополнительные аргументы для стабильности
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # 5. Указываем путь к драйверу yandexdriver.exe
        driver_path = r'D:\ZERO\2025 12 15 OZON_BOT\Драйвер\yandexdriver.exe'
        service = Service(executable_path=driver_path)

        # 6. Создаём драйвер
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # 7. Маскируем автоматизацию
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print(f"✅ Яндекс.Браузер запущен через YandexDriver")
        return self.driver

    def close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            print("✅ Драйвер Chrome закрыт")

    def extract_product_id(self, url):
        """Извлекает ID товара из разных форматов ссылок Ozon"""
        url = url.strip()

        # Если короткая ссылка (ozon.ru/t/...)
        if '/t/' in url:
            try:
                print(f"  Обнаружена короткая ссылка, пробую редирект...")
                # Используем head-запрос для редиректа без полной загрузки
                self.driver.get(url)
                time.sleep(2)
                url = self.driver.current_url
                print(f"  Перенаправлено на: {url}")
            except Exception as e:
                print(f"  Ошибка редиректа: {e}")

        # ПАТТЕРНЫ В ПРИОРИТЕТНОМ ПОРЯДКЕ:
        patterns = [
            r'/product/(\d+)/',  # 1. /product/123456/
            r'-(\d+)/?$',  # 2. ...-123456/ (ИЩЕМ ЧИСЛА ПОСЛЕ ПОСЛЕДНЕГО ДЕФИСА)
            r'[?&]productId=(\d+)',  # 3. ?productId=123456
            r'[?&]id=(\d+)',  # 4. ?id=123456
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                product_id = match.group(1)
                print(f"✅ Найден ID '{product_id}' по паттерну: {pattern}")
                return product_id

        print(f"❌ Не удалось найти ID в URL: {url}")
        return None

    def get_product_info(self, url):
        """
        Основной метод получения информации о товаре

        :return: dict с информацией о товаре или None
        """
        print(f"\n🔍 Парсим URL: {url}")

        # Запускаем драйвер если ещё не запущен
        if not self.driver:
            self.setup_driver()

        product_id = self.extract_product_id(url)

        if not product_id:
            print("❌ Не удалось извлечь ID товара")
            return None

        try:
            # Формируем правильный URL
            product_url = f"https://www.ozon.ru/product/{product_id}/"
            print(f"📦 Открываю страницу товара: {product_url}")

            # Открываем страницу
            self.driver.get(product_url)

            # Ждём загрузки страницы
            time.sleep(3)  # Базовая задержка

            # Ожидаем загрузки основных элементов
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
                print("✅ Страница загрузилась")
            except TimeoutException:
                print("⚠️ Страница загрузилась медленно, продолжаем...")

            # Делаем скролл для загрузки контента
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(1)

            # Получаем данные
            product_info = self._extract_product_data()

            if product_info:
                product_info['product_id'] = product_id
                product_info['url'] = product_url
                return product_info
            else:
                print("❌ Не удалось извлечь данные")
                return None

        except Exception as e:
            print(f"⚠️ Ошибка при парсинге: {e}")
            return None

    def _extract_product_data(self):
        """Извлечение данных о товаре со страницы (С ОЖИДАНИЕМ)"""
        print("🔍 Начинаю извлечение данных о товаре...")

        try:
            # ВАЖНО: Даём время на загрузку динамического контента
            print("   Ожидаю загрузку динамического контента (3 секунды)...")
            import time
            time.sleep(3)  # Ждём 3 секунды

            # Дополнительно: делаем небольшой скролл, чтобы активировать загрузку
            self.driver.execute_script("window.scrollTo(0, 200);")
            time.sleep(1)  # Ждём ещё секунду после скролла

            # 1. Извлекаем название
            print("   Шаг 1: Извлекаю название...")
            title = self._extract_title()

            # 2. Извлекаем цену
            print("   Шаг 2: Извлекаю цену...")
            price = self._extract_price()

            # 3. Проверяем наличие товара
            print("   Шаг 3: Проверяю наличие...")
            availability = self._check_availability()

            print(f"✅ Все данные извлечены. Название: '{title[:50]}...', Цена: {price}")

            return {
                'name': title,
                'price': price,
                'available': availability
            }

        except Exception as e:
            print(f"⚠️ Ошибка в _extract_product_data: {e}")
            import traceback
            traceback.print_exc()
            return {
                'name': "Неизвестный товар (ошибка)",
                'price': None,
                'available': False
            }

    def _extract_title(self):
        """Извлечение названия товара (улучшенная версия с ожиданием)"""
        print("🔍 Ищу название товара...")

        # Сначала дадим время на загрузку
        import time
        time.sleep(1)

        # Приоритетные селекторы
        title_selectors = [
            ("css selector", "h1"),  # Основной заголовок
            ("css selector", "[data-widget='webProductHeading']"),  # Виджет
            ("css selector", "[data-widget='webProductHeading'] h1"),  # Заголовок внутри виджета
            ("css selector", ".product-page__title"),  # Класс заголовка
        ]

        for by, value in title_selectors:
            try:
                # Явное ожидание элемента (до 5 секунд)
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((by, value))
                )

                if element and element.text.strip():
                    title = element.text.strip()
                    title = ' '.join(title.split())  # Убираем лишние пробелы
                    print(f"✅ Название найдено (селектор: {by}='{value}'): {title[:80]}...")
                    return title

            except Exception as e:
                # Если элемент не найден, пробуем следующий селектор
                continue

        print("⚠️ Название не найдено ни одним из селекторов")
        return "Неизвестный товар"

    def _extract_price(self):
        """Извлечение цены товара - упрощённая отладочная версия"""
        print("🔍 [DEBUG] Запущен метод _extract_price")

        # 1. Попробуем найти основной виджет цены
        try:
            price_widget = self.driver.find_element("css selector", "[data-widget='webPrice']")
            widget_html = price_widget.get_attribute('outerHTML')[:300]
            widget_text = price_widget.text
            print(f"   [DEBUG] Найден виджет webPrice.")
            print(f"   [DEBUG] Его текст: '{widget_text}'")
            print(f"   [DEBUG] Его HTML (первые 300 символов): {widget_html}")

            # Попробуем найти внутри виджета элемент с конкретным классом, содержащий основную цену
            # Часто это span с классом, содержащим 'price' или 'numeric'
            inner_selectors = [
                "span", "div", "b", "strong"
            ]

            for tag in inner_selectors:
                try:
                    elements = price_widget.find_elements("css selector", tag)
                    for i, elem in enumerate(elements):
                        elem_text = elem.text.strip()
                        if elem_text and any(c.isdigit() for c in elem_text):
                            print(f"   [DEBUG] Внутренний элемент <{tag}>[{i}]: '{elem_text}'")
                            # Пробуем вытащить первую цену из этого текста
                            import re
                            match = re.search(r'(\d[\d\s\u2009]*)', elem_text)
                            if match:
                                price_str = re.sub(r'[\s\u2009]+', '', match.group(1))
                                try:
                                    price = float(price_str)
                                    print(f"✅ Цена извлечена из внутреннего элемента: {price}₽")
                                    return price
                                except:
                                    continue
                except:
                    continue

        except Exception as e:
            print(f"   [DEBUG] Виджет webPrice не найден или ошибка: {e}")

        # 2. Резервный поиск: ищем любой элемент с текстом, похожим на цену со знаком рубля
        print("   [DEBUG] Пробую резервный поиск по всей странице...")
        try:
            all_elements = self.driver.find_elements("css selector", "*")
            for elem in all_elements[:100]:  # Проверяем первые 100 элементов
                text = elem.text.strip()
                if '₽' in text and any(c.isdigit() for c in text):
                    print(f"   [DEBUG] Найден элемент с текстом '₽': '{text[:50]}'")
                    import re
                    match = re.search(r'(\d[\d\s\u2009]*)\s*₽', text)
                    if match:
                        price_str = re.sub(r'[\s\u2009]+', '', match.group(1))
                        try:
                            price = float(price_str)
                            print(f"✅ Цена найдена через резервный поиск: {price}₽")
                            return price
                        except:
                            continue
        except Exception as e:
            print(f"   [DEBUG] Ошибка при резервном поиске: {e}")

        print("❌ Цена не найдена")
        return None

    def _check_availability(self):
        """Проверка наличия товара"""
        try:
            # Селекторы для проверки наличия
            availability_selectors = [
                "[data-testid='out-of-stock']",
                ".out-of-stock",
                ".unavailable",
                "[aria-label*='нет в наличии']",
                "[data-testid='add-to-cart-button']",
            ]

            for selector in availability_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.lower()
                        if 'нет' in text or 'out' in text or 'недоступ' in text:
                            print("⚠️ Товар отсутствует в наличии")
                            return False
                        elif 'купить' in text or 'корзину' in text or 'cart' in text:
                            print("✅ Товар в наличии")
                            return True
                except:
                    continue

            return True  # По умолчанию считаем что в наличии

        except Exception as e:
            print(f"Ошибка проверки наличия: {e}")
            return True

    def save_screenshot(self, filename="ozon_screenshot.png"):
        """Сохранение скриншота для отладки"""
        try:
            self.driver.save_screenshot(filename)
            print(f"📸 Скриншот сохранён: {filename}")
        except Exception as e:
            print(f"Ошибка сохранения скриншота: {e}")

    def get_page_source(self):
        """Получение исходного кода страницы"""
        return self.driver.page_source