DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '機器人'
) THEN PERFORM fs_insert_class(1, 4, '機器人', '機器人Class', NULL);
END IF;
END $$;