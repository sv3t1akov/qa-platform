#!/usr/bin/env python3
"""
Скрипт генерации полных данных товаров из products_1_1000.txt
Генерирует недостающие поля: sku, price, category, description, rating, reviewCount
"""

import random
import json
from pathlib import Path

# Категории товаров и их бренды (из анализа)
CATEGORIES = {
    "ELECTRONICS": {
        "brands": ["iPhone", "Samsung", "Sony", "LG", "Xiaomi"],
        "price_range": (50000, 500000),
        "descriptions": [
            "Современное устройство с передовыми технологиями",
            "Высокое качество и надёжность",
            "Инновационные функции и стильный дизайн",
            "Профессиональное оборудование",
            "Популярная модель с отличными отзывами"
        ]
    },
    "FASHION": {
        "brands": ["Nike", "Adidas", "Zara", "H&M", "Gucci"],
        "price_range": (5000, 150000),
        "descriptions": [
            "Стильная и модная вещь",
            "Качественные материалы",
            "Трендовая модель сезона",
            "Комфортная и практичная",
            "Элегантный дизайн"
        ]
    },
    "HOME": {
        "brands": ["IKEA", "Dyson", "Philips", "Bosch", "Tefal"],
        "price_range": (10000, 300000),
        "descriptions": [
            "Для комфорта в доме",
            "Практичное решение для быта",
            "Качественная бытовая техника",
            "Современный дизайн",
            "Надёжное оборудование"
        ]
    },
    "BEAUTY": {
        "brands": ["L'Oreal", "Maybelline", "MAC", "Clinique"],
        "price_range": (2000, 50000),
        "descriptions": [
            "Качественная косметика",
            "Проверенные ингредиенты",
            "Профессиональный уход",
            "Популярный продукт",
            "Эффективное средство"
        ]
    },
    "FOOD": {
        "brands": ["Organic", "Bio", "Natural", "Fresh"],
        "price_range": (500, 20000),
        "descriptions": [
            "Натуральные продукты",
            "Без консервантов",
            "Высокое качество",
            "Свежие ингредиенты",
            "Полезно для здоровья"
        ]
    }
}

def generate_product_data(products_file_path: Path, output_json_path: Path = None):
    """
    Генерирует полные данные товаров из файла products_1_1000.txt
    
    Args:
        products_file_path: Путь к файлу products_1_1000.txt
        output_json_path: Опциональный путь для сохранения JSON (если None, не сохраняет)
    """
    products = {}
    
    if not products_file_path.exists():
        print(f"Файл {products_file_path} не найден!")
        return products
    
    with open(products_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ':' not in line:
                continue
            
            try:
                idx = line.index(':')
                pid = int(line[:idx].strip())
                name = line[idx + 1:].strip()
                
                if 1 <= pid <= 1000:
                    # Выбираем случайную категорию
                    category = random.choice(list(CATEGORIES.keys()))
                    cat_info = CATEGORIES[category]
                    
                    # Генерируем данные
                    brand = random.choice(cat_info["brands"])
                    price_min, price_max = cat_info["price_range"]
                    price = random.randint(price_min, price_max)
                    
                    # SKU формат: {CATEGORY[:4]}-{ID:03d}
                    sku = f"{category[:4]}-{pid:03d}"
                    
                    # Описание
                    description = random.choice(cat_info["descriptions"])
                    
                    # Рейтинг 3.5-5.0 с шагом 0.1
                    rating = round(random.uniform(3.5, 5.0), 1)
                    
                    # Количество отзывов 0-500
                    review_count = random.randint(0, 500)
                    
                    # В наличии в 75% случаев
                    in_stock = random.random() < 0.75
                    
                    products[pid] = {
                        "id": pid,
                        "productId": str(pid),
                        "sku": sku,
                        "name": name,
                        "description": description,
                        "price": price,
                        "currency": "KZT",
                        "category": category,
                        "inStock": in_stock,
                        "rating": rating,
                        "reviewCount": review_count
                    }
            except (ValueError, IndexError):
                continue
    
    if output_json_path:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"Данные сохранены в {output_json_path}")
    
    return products


if __name__ == "__main__":
    # Пути относительно корня лабы
    lab_root = Path(__file__).resolve().parent.parent
    products_file = lab_root / "products_1_1000.txt"
    output_file = lab_root / "products_full.json"
    
    products = generate_product_data(products_file, output_file)
    print(f"Сгенерировано {len(products)} товаров")
