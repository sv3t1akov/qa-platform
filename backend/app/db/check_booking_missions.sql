-- Проверка наличия Booking T1 миссий в базе данных

-- Проверка домена
SELECT 'Domain check:' as info;
SELECT id, name, icon, description FROM domains WHERE id = 'booking';

-- Проверка миссий
SELECT 'Missions check:' as info;
SELECT id, domain_id, tier, title, bugs, base_url 
FROM missions 
WHERE domain_id = 'booking' 
ORDER BY sort_order;

-- Проверка багов
SELECT 'Bugs check:' as info;
SELECT b.id, b.mission_id, b.title, b.flag, b.points, b.active
FROM bugs b
JOIN missions m ON b.mission_id = m.id
WHERE m.domain_id = 'booking'
ORDER BY m.sort_order, b.sort_order;

-- Статистика
SELECT 'Statistics:' as info;
SELECT 
    COUNT(DISTINCT m.id) as total_missions,
    COUNT(DISTINCT b.id) as total_bugs,
    SUM(CASE WHEN b.active = true THEN 1 ELSE 0 END) as active_bugs
FROM missions m
LEFT JOIN bugs b ON b.mission_id = m.id
WHERE m.domain_id = 'booking';
