import requests
import re
import json
import time
from urllib.parse import urlparse
from .config import Config


class OzonParser:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()

        # Более полные заголовки, как у реального браузера
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })

        # Устанавливаем таймауты
        self.timeout = 15

    def extract_product_id(self, url):
        """Извлекает ID товара из разных форматов ссылок Ozon"""
        url = url.strip()

        # Если короткая ссылка (ozon.ru/t/...)
        if '/t/' in url:
            try:
                # Следуем по редиректу
                response = self.session.head(
                    url,
                    allow_redirects=True,
                    timeout=self.timeout
                )
                url = response.url
                print(f"Перенаправлено на: {url}")
            except Exception as e:
                print(f"Ошибка редиректа: {e}")

        # Паттерны для поиска ID
        patterns = [
            r'/product/(\d+)/',  # /product/123456/
            r'--(\d+)/?$',  # товар-123456/
            r'[?&]productId=(\d+)',  # ?productId=123456
            r'[?&]id=(\d+)',  # ?id=123456
            r'/(\d+)/?$',  # /123456/
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                product_id = match.group(1)
                print(f"Найден ID: {product_id} по паттерну {pattern}")
                return product_id

        print(f"Не удалось найти ID в URL: {url}")
        return None

    def get_product_info(self, url):
        """Основной метод получения информации о товаре"""
        print(f"\nПарсим URL: {url}")

        # Получаем ID товара
        product_id = self.extract_product_id(url)
        if not product_id:
            print("❌ Не удалось извлечь ID товара")
            return None

        # Пробуем несколько методов по порядку
        methods = [
            self._try_direct_html,  # Прямой парсинг HTML
            self._try_graphql_api,  # GraphQL API
            self._try_mobile_api,  # Мобильное API
        ]

        for method in methods:
            print(f"\nПробуем метод: {method.__name__}")
            result = method(url, product_id)
            if result and result.get('price'):
                print(f"✅ Успех через {method.__name__}")
                return result
            elif result:
                print(f"⚠️ Метод {method.__name__} вернул данные без цены")
                # Возвращаем хотя бы название
                return result

        print("❌ Все методы не сработали")
        return None

    def _try_direct_html(self, url, product_id):
        """Прямой парсинг HTML страницы"""
        try:
            # Используем полную ссылку с ID
            full_url = f"https://www.ozon.ru/product/{product_id}/"

            response = self.session.get(
                full_url,
                timeout=self.timeout,
                allow_redirects=True
            )

            if response.status_code != 200:
                print(f"HTTP {response.status_code} для {full_url}")
                return None

            html = response.text

            # Ищем данные в JSON-LD формате (самый надёжный способ)
            json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
            json_ld_matches = re.findall(json_ld_pattern, html, re.DOTALL)

            for json_ld in json_ld_matches:
                try:
                    data = json.loads(json_ld)
                    if data.get('@type') == 'Product':
                        name = data.get('name', 'Неизвестный товар')

                        # Пытаемся получить цену
                        offers = data.get('offers', {})
                        price = None

                        if isinstance(offers, dict):
                            price_str = offers.get('price')
                            if price_str:
                                try:
                                    price = float(price_str)
                                except:
                                    pass

                        if price:
                            return {
                                'product_id': product_id,
                                'name': name,
                                'price': price,
                                'url': full_url
                            }
                        else:
                            # Хотя бы возвращаем название
                            return {
                                'product_id': product_id,
                                'name': name,
                                'price': None,
                                'url': full_url
                            }
                except json.JSONDecodeError:
                    continue

            # Если JSON-LD не нашли, ищем в HTML
            name = self._extract_name_from_html(html)
            price = self._extract_price_from_html(html)

            if name:
                return {
                    'product_id': product_id,
                    'name': name,
                    'price': price,
                    'url': full_url
                }

        except Exception as e:
            print(f"Ошибка в _try_direct_html: {e}")

        return None

    def _try_graphql_api(self, url, product_id):
        """Попытка через GraphQL API Ozon"""
        try:
            graphql_url = "https://www.ozon.ru/api/entrypoint-api.bx/graphql"

            # GraphQL запрос для получения данных товара
            graphql_query = {
                "query": """
                query GetProduct($productId: ID!) {
                    product(id: $productId) {
                        id
                        title
                        price {
                            price
                            formattedPrice
                        }
                    }
                }
                """,
                "variables": {
                    "productId": product_id
                },
                "operationName": "GetProduct"
            }

            headers = {
                **self.session.headers,
                'Content-Type': 'application/json',
                'Origin': 'https://www.ozon.ru',
                'Referer': f'https://www.ozon.ru/product/{product_id}/',
                'x-o3-app-name': 'website',
            }

            response = self.session.post(
                graphql_url,
                json=graphql_query,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                product_data = data.get('data', {}).get('product', {})

                if product_data:
                    name = product_data.get('title', 'Неизвестный товар')
                    price_info = product_data.get('price', {})

                    price = None
                    if isinstance(price_info, dict):
                        price_str = price_info.get('price')
                        if price_str:
                            try:
                                price = float(price_str)
                            except:
                                pass

                    if name:
                        return {
                            'product_id': product_id,
                            'name': name,
                            'price': price,
                            'url': f'https://www.ozon.ru/product/{product_id}/'
                        }

        except Exception as e:
            print(f"Ошибка в _try_graphql_api: {e}")

        return None

    def _try_mobile_api(self, url, product_id):
        """Мобильное API (резервный метод)"""
        try:
            api_url = "https://api.ozon.ru/composer-api.bx/_action/productDetailV2"

            headers = {
                **self.session.headers,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'https://www.ozon.ru',
                'Referer': f'https://www.ozon.ru/product/{product_id}/',
            }

            payload = {
                "productId": product_id,
                "clientFeatures": ["webp"],
                "layout": "SINGLE_PRODUCT"
            }

            response = self.session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()

                # Пытаемся найти продукт в ответе
                product = data.get('product') or data.get('widgetStates', {})

                if isinstance(product, dict):
                    name = product.get('title') or product.get('name', 'Неизвестный товар')

                    # Ищем цену в разных форматах
                    price = None

                    # Вариант 1: Прямо в объекте продукта
                    price_info = product.get('price')
                    if isinstance(price_info, dict):
                        price_str = price_info.get('price') or price_info.get('value')
                        if price_str:
                            try:
                                price = float(str(price_str).replace(' ', '').replace(',', '.'))
                            except:
                                pass

                    # Вариант 2: Ищем в строковом представлении
                    if not price:
                        data_str = json.dumps(data)
                        price_match = re.search(r'"price":\s*["\']?(\d+(?:[.,]\d+)?)', data_str)
                        if price_match:
                            try:
                                price = float(price_match.group(1).replace(',', '.'))
                            except:
                                pass

                    if name:
                        return {
                            'product_id': product_id,
                            'name': name[:200],  # Ограничиваем длину
                            'price': price,
                            'url': f'https://www.ozon.ru/product/{product_id}/'
                        }

        except Exception as e:
            print(f"Ошибка в _try_mobile_api: {e}")

        return None

    def _extract_name_from_html(self, html):
        """Извлекаем название из HTML"""
        patterns = [
            r'<h1[^>]*>(.*?)</h1>',
            r'"title":"([^"]+)"',
            r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
            r'<title>([^<]+)</title>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Очищаем от HTML тегов
                name = re.sub(r'<[^>]+>', '', name)
                name = re.sub(r'&[a-z]+;', ' ', name)
                return name[:200]

        return None

    def _extract_price_from_html(self, html):
        """Извлекаем цену из HTML"""
        patterns = [
            r'"price":\s*["\']?(\d+(?:[.,]\d+)?)',
            r'"finalPrice":\s*(\d+(?:[.,]\d+)?)',
            r'data-price=["\']?(\d+(?:[.,]\d+)?)',
            r'<span[^>]*data-testid="price"[^>]*>.*?(\d[\d\s]*)\s*₽',
            r'<meta[^>]*property="product:price:amount"[^>]*content="([^"]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                try:
                    # Очищаем строку от пробелов и заменяем запятую на точку
                    price_str = str(match).replace(' ', '').replace(',', '.')
                    price = float(price_str)
                    return price
                except ValueError:
                    continue

        return None