-- Миграция: пересчет рангов для существующих пользователей
-- Обновляет поле current_rank_id в таблице users на основе их total_points
-- Выполняется только если поле current_rank_id существует

DO $$
DECLARE
    user_record RECORD;
    calculated_rank_id VARCHAR(50);
BEGIN
    -- Проверяем, существует ли поле current_rank_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'current_rank_id'
    ) THEN
        -- Пересчитываем ранги для всех пользователей
        FOR user_record IN 
            SELECT 
                u.id,
                COALESCE(
                    -- Пересчитываем total_points по тирам миссий найденных флагов
                    (
                        SELECT SUM(
                            CASE 
                                WHEN m.tier = 'T1' THEN 10
                                WHEN m.tier = 'T2' THEN 20
                                WHEN m.tier = 'T3' THEN 30
                                WHEN m.tier = 'T4' THEN 40
                                WHEN m.tier = 'T5' THEN 50
                                ELSE 10
                            END
                        )
                        FROM user_found_flags uff
                        JOIN bugs b ON b.id = uff.bug_id
                        JOIN missions m ON m.id = b.mission_id
                        WHERE uff.user_id = u.id
                    ),
                    0
                ) as total_points
            FROM users u
        LOOP
            -- Находим ранг на основе total_points
            -- Используем логику из calculate_rank: находим последний ранг, где min_points <= total_points
            SELECT r.id INTO calculated_rank_id
            FROM ranks r
            WHERE r.min_points <= user_record.total_points
            ORDER BY r.min_points DESC
            LIMIT 1;
            
            -- Обновляем current_rank_id для пользователя
            UPDATE users
            SET current_rank_id = calculated_rank_id
            WHERE id = user_record.id;
        END LOOP;
        
        RAISE NOTICE 'Ранги пересчитаны для всех пользователей';
    ELSE
        RAISE NOTICE 'Поле current_rank_id не существует в таблице users. Миграция пропущена.';
    END IF;
END $$;
