CREATE OR REPLACE PROCEDURE sp_insert_module_setting(
    _bot_class_id INT,
    _module_name TEXT,
    _is_enabled BOOLEAN DEFAULT FALSE,
    _version VARCHAR(20) DEFAULT '1.0.0',
    _description TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    _setting_class_id INT;
    _object_id INT;
BEGIN
    -- 獲取設定類別 ID
    SELECT
        child_class_id
    INTO
        _setting_class_id
    FROM
        vs_sub_class
    WHERE
        class_id = _bot_class_id
        AND entity_id = 5
    LIMIT 1;

    -- 若找不到設定類別 ID，則拋出異常
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: 找不到 % 底下的 Setting Class', _bot_class_id;
    END IF;

    -- 檢查是否已存在該模組名稱
    SELECT
        ms.object_id
    INTO
        _object_id
    FROM
        vs_module_settings ms
    WHERE
        ms.class_id = _setting_class_id
        AND ms.chinese_name = _module_name
    LIMIT 1;

    -- 如果找到，更新 is_enabled
    IF FOUND THEN
        UPDATE module_settings
        SET is_enabled = _is_enabled
        WHERE object_id = _object_id;
    ELSE
        -- 如果未找到，執行插入流程
        -- 插入新的物件名稱，並返回物件 ID
        INSERT INTO objects (chinese_name)
        VALUES (_module_name)
        RETURNING object_id INTO _object_id;

        -- 建立類別與物件的關聯
        INSERT INTO class_object_relations (class_id, object_id)
        VALUES (_setting_class_id, _object_id);

        -- 插入模組設定
        INSERT INTO module_settings (object_id, is_enabled, version, description)
        VALUES (_object_id, _is_enabled, _version, _description);
    END IF;
END;
$$;
