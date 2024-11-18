CREATE OR REPLACE PROCEDURE sp_insert_entity(IN _chinese_name VARCHAR(50) DEFAULT NULL, IN _english_name VARCHAR(50) DEFAULT NULL, IN _is_relational BOOLEAN DEFAULT NULL)
LANGUAGE plpgsql
AS $$
BEGIN
    -- 檢查參數是否為空
    IF(_chinese_name IS NULL OR _english_name IS NULL OR _is_relational IS NULL) THEN
        RAISE EXCEPTION 'Error: 所有參數 (chinese_name, english_name, is_relational) 都必須提供';
    END IF;
    -- 檢查 chinese_name 或 english_name 是否已存在
    IF EXISTS(
        SELECT
            1
        FROM
            entities
        WHERE
            entities.chinese_name = _chinese_name
            OR entities.english_name = _english_name) THEN
    RAISE EXCEPTION 'Error: chinese_name 或 english_name 已經存在，無法建立 entity';
END IF;
            -- 插入數據到 entities 表中
            INSERT INTO entities(
                chinese_name,
                english_name,
                is_relational)
            VALUES(
                _chinese_name,
                _english_name,
                _is_relational);
END;
$$;

