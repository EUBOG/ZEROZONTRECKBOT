# test_check_prices_fixed.py
from bot.database import Database, Product  # Импортируем Product напрямую
from decimal import Decimal

db = Database()

# Получаем все товары
products = db.session.query(Product).all()  # Используем Product напрямую

print(f"Найдено товаров: {len(products)}")
print("=" * 80)

for p in products:
    print(f"\nID: {p.id}")
    print(f"Название: {p.name}")
    print(f"URL: {p.url}")
    print(f"current_price: {p.current_price}")
    print(f"previous_price: {p.previous_price}")

    # Проверяем и исправляем если есть проблемы с плавающей точкой
    needs_fix = False

    if p.current_price is not None:
        # Округляем до 2 знаков
        rounded_current = round(p.current_price, 2)
        if abs(p.current_price - rounded_current) > 0.001:
            print(f"  ⚠️ Исправляю current_price: {p.current_price} -> {rounded_current}")
            p.current_price = rounded_current
            needs_fix = True

    if p.previous_price is not None:
        # Округляем до 2 знаков
        rounded_previous = round(p.previous_price, 2)
        if abs(p.previous_price - rounded_previous) > 0.001:
            print(f"  ⚠️ Исправляю previous_price: {p.previous_price} -> {rounded_previous}")
            p.previous_price = rounded_previous
            needs_fix = True

    # Также можно использовать Decimal для более точного отображения
    if p.current_price:
        dec_current = Decimal(str(p.current_price)).quantize(Decimal('0.01'))
        print(f"  Точное значение (Decimal): {dec_current}")

if needs_fix:
    db.session.commit()
    print("\n✅ Все цены округлены до 2 знаков после запятой")
else:
    print("\n✅ Все цены в порядке")

print("\n" + "=" * 80)
print("Сводка по всем товарам:")
for p in products:
    print(f"{p.id:3} | {p.name[:40]:40} | current: {p.current_price:8.2f} | previous: {p.previous_price:8.2f}")