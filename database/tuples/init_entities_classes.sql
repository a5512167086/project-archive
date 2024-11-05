DO $$ BEGIN -- insert entities
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '商業用戶'
) THEN CALL sp_insert_entity('商業用戶', 'BusinessUser', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '客戶用戶'
) THEN CALL sp_insert_entity('客戶用戶', 'CustomerUser', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '權限角色'
) THEN CALL sp_insert_entity('權限角色', 'Role', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '機器人'
) THEN CALL sp_insert_entity('機器人', 'Bot', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '指令'
) THEN CALL sp_insert_entity('指令', 'Command', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '設定'
) THEN CALL sp_insert_entity('設定', 'Setting', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '訊息紀錄'
) THEN CALL sp_insert_entity('訊息紀錄', 'MessageLog', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '產品'
) THEN CALL sp_insert_entity('產品', 'Product', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '知識'
) THEN CALL sp_insert_entity('知識', 'Knowledge', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '訂單'
) THEN CALL sp_insert_entity('訂單', 'Order', TRUE);
END IF;
IF NOT EXISTS (
    SELECT 1
    FROM entities
    WHERE chinese_name = '預約'
) THEN CALL sp_insert_entity('預約', 'Reservation', TRUE);
END IF;
END $$;