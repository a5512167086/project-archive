CREATE OR REPLACE FUNCTION fs_insert_bot(_bot_name varchar(50), _channel_id varchar(100), _channel_access_token varchar(100), _channel_secret varchar(100), _owner_id uuid)
    RETURNS TABLE(
        bot_detail_id uuid,
        class_id int,
        object_id int,
        chinese_name varchar(50),
        owner_id uuid
    )
    AS $$
DECLARE
    new_class_id int;
    object_id int;
    -- 保留原變數名稱
BEGIN
    -- 驗證輸入參數是否為 NULL
    IF (_bot_name IS NULL OR _channel_id IS NULL OR _channel_access_token IS NULL OR _channel_secret IS NULL OR _owner_id IS NULL) THEN
        RAISE EXCEPTION 'Error: 所有參數 (_bot_name, _channel_id, _channel_access_token, _channel_secret, _owner_id) 都必須提供';
    END IF;
    -- 呼叫 fs_insert_class 並取得 new_class_id
    SELECT
        fs_insert_class(2, 3, '', '用戶創建的機器人', _owner_id) INTO new_class_id;
    -- 插入到 objects 表並取得 object_id
    INSERT INTO objects(chinese_name, owner_id)
        VALUES (_bot_name, _owner_id)
    RETURNING
        objects.object_id INTO object_id;
    -- 明確指定表字段
    -- 插入到 bot_details 表
    INSERT INTO bot_details(object_id, channel_id, channel_access_token, channel_secret)
        VALUES (object_id, _channel_id, _channel_access_token, _channel_secret)
    RETURNING
        bot_details.bot_detail_id INTO bot_detail_id;
    -- 插入到 class_object_relations 表
    INSERT INTO class_object_relations(class_id, object_id)
        VALUES (new_class_id, object_id);
    -- 插入其他相關 class
    PERFORM
        fs_insert_class(new_class_id, 5, '指令', '自動回覆指令', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 6, '設定', '跟Module功能有關的設定', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 7, '訊息紀錄', '訊息紀錄', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 8, '產品', '電商功能的產品', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 9, '知識', '問答功能的知識', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 10, '訂單', '電商功能的訂單', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 11, '預約', '預約功能的預約', _owner_id);
    -- 呼叫 sp_rename_class，傳遞 new_class_id 和 object_id
    CALL sp_rename_class(new_class_id, CAST(object_id AS text));
    -- 返回結果
    RETURN QUERY
    SELECT
        bot_detail_id,
        new_class_id,
        object_id,
        _bot_name,
        _owner_id;
END;
$$
LANGUAGE plpgsql;

