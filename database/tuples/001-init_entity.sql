DO $$ BEGIN IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '資源'
) THEN CALL sp_insert_entity('資源', 'Resource', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '機器人'
) THEN CALL sp_insert_entity('機器人', 'Bot', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '設定'
) THEN CALL sp_insert_entity('設定', 'Setting', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '訊息紀錄'
) THEN CALL sp_insert_entity('訊息紀錄', 'MessageLog', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '產品'
) THEN CALL sp_insert_entity('產品', 'Product', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '知識'
) THEN CALL sp_insert_entity('知識', 'Knowledge', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '訂單'
) THEN CALL sp_insert_entity('訂單', 'Order', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '預約'
) THEN CALL sp_insert_entity('預約', 'Reservation', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '服務'
) THEN CALL sp_insert_entity('服務', 'Service', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '類別'
) THEN CALL sp_insert_entity('類別', 'Category', TRUE);

END IF;

IF NOT EXISTS(
    SELECT 1
    FROM entities
    WHERE chinese_name = '品牌'
) THEN CALL sp_insert_entity('品牌', 'Brand', TRUE);

END IF;

END $$;