DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '機器人'
) THEN PERFORM fs_insert_class(1, 4, '機器人', '機器人Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '權限'
) THEN PERFORM fs_insert_class(1, 3, '權限', '權限Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '指令'
) THEN PERFORM fs_insert_class(2, 5, '指令', '指令Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '模組'
) THEN PERFORM fs_insert_class(2, 6, '模組', '模組Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '訊息紀錄'
) THEN PERFORM fs_insert_class(2, 7, '訊息紀錄', '訊息紀錄Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '類別'
) THEN PERFORM fs_insert_class(2, 8, '類別', '類別Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '產品'
) THEN PERFORM fs_insert_class(7, 8, '產品', '產品Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '知識'
) THEN PERFORM fs_insert_class(2, 9, '知識', '知識Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '客戶'
) THEN PERFORM fs_insert_class(2, 2, '客戶', '客戶Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '訂單'
) THEN PERFORM fs_insert_class(10, 10, '訂單', '訂單Class', NULL);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '預約'
) THEN PERFORM fs_insert_class(10, 11, '預約', '訂單Class', NULL);
END IF;
END $$;