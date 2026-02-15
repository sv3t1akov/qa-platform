#!/usr/bin/env python3
"""
Скрипт для подсчета статистики по миссиям и сравнения с системой рангов.

Использование:
    python scripts/calculate_missions_stats.py
"""

import re
import os
from pathlib import Path

# Баллы за тир
POINTS_BY_TIER = {'T1': 10, 'T2': 20, 'T3': 30, 'T4': 40, 'T5': 50}

# Система рангов
RANKS = [
    {'id': 'newbie', 'nameRu': 'Новичок', 'minPoints': 0},
    {'id': 'trainee', 'nameRu': 'Стажёр', 'minPoints': 30},
    {'id': 'seeker', 'nameRu': 'Искатель', 'minPoints': 75},
    {'id': 'tracker', 'nameRu': 'Следопыт', 'minPoints': 140},
    {'id': 'tester', 'nameRu': 'Тестировщик', 'minPoints': 230},
    {'id': 'bug_hunter', 'nameRu': 'Охотник за багами', 'minPoints': 350},
    {'id': 'explorer', 'nameRu': 'Исследователь', 'minPoints': 500},
    {'id': 'qa_engineer', 'nameRu': 'QA-инженер', 'minPoints': 700},
    {'id': 'detective', 'nameRu': 'Детектив', 'minPoints': 950},
    {'id': 'specialist', 'nameRu': 'Специалист', 'minPoints': 1250},
    {'id': 'bug_slayer', 'nameRu': 'Истребитель багов', 'minPoints': 1650},
    {'id': 'expert', 'nameRu': 'Эксперт', 'minPoints': 2150},
    {'id': 'senior_tester', 'nameRu': 'Старший тестировщик', 'minPoints': 2800},
    {'id': 'test_architect', 'nameRu': 'Архитектор тестов', 'minPoints': 3650},
    {'id': 'qa_master', 'nameRu': 'Мастер QA', 'minPoints': 4750},
    {'id': 'legend', 'nameRu': 'Легенда', 'minPoints': 6500},
]


def parse_missions_from_sql(file_path):
    """Парсит SQL файл и извлекает информацию о миссиях."""
    missions = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем все INSERT INTO missions
    # Паттерн для поиска: 'ecom-...', tier, ..., bugs
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Ищем строку с mission_id
        if "'ecom-" in line or "'fintech-" in line or "'booking-" in line or "'marketplace-" in line or "'healthcare-" in line or "'social-" in line:
            mission_id_match = re.search(r"'([a-z]+-[^']+)'", line)
            if mission_id_match:
                mission_id = mission_id_match.group(1)
                
                # Ищем tier и bugs в текущей и следующих строках
                tier = None
                bugs = None
                
                for j in range(i, min(i + 10, len(lines))):
                    tier_match = re.search(r"'([T]\d+)'", lines[j])
                    if tier_match:
                        tier = tier_match.group(1)
                    
                    # Ищем bugs - обычно это число перед запятой в последовательности чисел
                    bugs_match = re.search(r"(\d+),\s*(\d+),", lines[j])
                    if bugs_match:
                        # Второе число обычно bugs
                        bugs = int(bugs_match.group(2))
                        break
                
                if tier and bugs is not None:
                    missions.append({
                        'id': mission_id,
                        'tier': tier,
                        'bugs': bugs
                    })
        i += 1
    
    return missions


def calculate_stats():
    """Подсчитывает статистику по всем миссиям."""
    # Находим все SQL файлы с миссиями
    backend_dir = Path(__file__).parent.parent
    db_dir = backend_dir / 'app' / 'db'
    
    sql_files = [
        db_dir / 'seed_missions.sql',
        db_dir / 'seed.sql',
    ]
    
    all_missions = []
    for sql_file in sql_files:
        if sql_file.exists():
            missions = parse_missions_from_sql(sql_file)
            all_missions.extend(missions)
    
    # Подсчитываем по тирам
    tiers = {}
    total_missions = 0
    total_bugs = 0
    
    for mission in all_missions:
        tier = mission['tier']
        bugs = mission['bugs']
        
        if tier not in tiers:
            tiers[tier] = {'missions': 0, 'bugs': 0}
        
        tiers[tier]['missions'] += 1
        tiers[tier]['bugs'] += bugs
        total_missions += 1
        total_bugs += bugs
    
    # Вычисляем баллы
    total_points = 0
    for tier in sorted(tiers.keys()):
        bugs = tiers[tier]['bugs']
        points_per_bug = POINTS_BY_TIER.get(tier, 0)
        tier_points = bugs * points_per_bug
        total_points += tier_points
    
    return {
        'tiers': tiers,
        'total_missions': total_missions,
        'total_bugs': total_bugs,
        'total_points': total_points
    }


def print_report(stats):
    """Выводит отчет по статистике."""
    print('=' * 70)
    print('СТАТИСТИКА ПО МИССИЯМ')
    print('=' * 70)
    print()
    
    tiers = stats['tiers']
    total_points = stats['total_points']
    
    for tier in sorted(tiers.keys()):
        missions_count = tiers[tier]['missions']
        bugs = tiers[tier]['bugs']
        points_per_bug = POINTS_BY_TIER.get(tier, 0)
        tier_points = bugs * points_per_bug
        
        print(f'{tier}:')
        print(f'  Миссий: {missions_count}')
        print(f'  Багов: {bugs}')
        print(f'  Баллов за баг: {points_per_bug}')
        print(f'  Всего баллов: {tier_points}')
        print()
    
    print('=' * 70)
    print(f'ИТОГО:')
    print(f'  Всего миссий: {stats["total_missions"]}')
    print(f'  Всего багов: {stats["total_bugs"]}')
    print(f'  Всего возможных баллов: {total_points}')
    print('=' * 70)
    print()
    
    # Сравнение с системой рангов
    print('=' * 70)
    print('СИСТЕМА РАНГОВ')
    print('=' * 70)
    max_rank_points = RANKS[-1]['minPoints']
    print(f'Максимальный ранг (Легенда): {max_rank_points} баллов')
    print(f'Доступно баллов из миссий: {total_points}')
    print()
    
    if total_points < max_rank_points:
        deficit = max_rank_points - total_points
        print(f'⚠️  НЕДОСТАТОК: Не хватает {deficit} баллов для достижения максимального ранга')
        print(f'   Нужно добавить примерно:')
        print(f'     - {deficit // 50 + (1 if deficit % 50 > 0 else 0)} багов T5')
        print(f'     - {deficit // 40 + (1 if deficit % 40 > 0 else 0)} багов T4')
        print(f'     - {deficit // 30 + (1 if deficit % 30 > 0 else 0)} багов T3')
        print(f'     - {deficit // 20 + (1 if deficit % 20 > 0 else 0)} багов T2')
    elif total_points > max_rank_points:
        excess = total_points - max_rank_points
        print(f'⚠️  ПЕРЕЛИМИТ: Превышение на {excess} баллов над максимальным рангом')
        print(f'   Можно убрать примерно:')
        print(f'     - {excess // 50} багов T5')
        print(f'     - {excess // 40} багов T4')
        print(f'     - {excess // 30} багов T3')
        print(f'     - {excess // 20} багов T2')
    else:
        print('✓ Идеальное соответствие!')
    print()
    
    # Показываем какой ранг можно достичь
    max_reachable = None
    for rank in reversed(RANKS):
        if total_points >= rank['minPoints']:
            max_reachable = rank
            print(f'Максимально достижимый ранг: {rank["nameRu"]} ({rank["minPoints"]} баллов)')
            break
    
    if max_reachable and total_points < max_rank_points:
        next_rank = None
        for rank in RANKS:
            if rank['minPoints'] > total_points:
                next_rank = rank
                break
        if next_rank:
            points_to_next = next_rank['minPoints'] - total_points
            print(f'До следующего ранга ({next_rank["nameRu"]}): {points_to_next} баллов')
    print()


if __name__ == '__main__':
    stats = calculate_stats()
    print_report(stats)
