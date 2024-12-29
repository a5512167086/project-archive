CREATE OR REPLACE FUNCTION fs_insert_bot(_bot_name varchar(50), _channel_id varchar(100), _channel_access_token varchar(100), _channel_secret varchar(100), _liff_id varchar(100), _owner_id uuid)
    RETURNS TABLE(
        bot_detail_id uuid,
        class_id int,
        object_id int,
        chinese_name varchar(50),
        channel_access_token varchar(100),
        liff_id varchar(100),
        owner_id uuid
    )
    AS $$
DECLARE
    new_class_id int;
    object_id int;
BEGIN
    IF (_bot_name IS NULL OR _channel_id IS NULL OR _channel_access_token IS NULL OR _channel_secret IS NULL OR _owner_id IS NULL) THEN
        RAISE EXCEPTION 'Error: 所有參數 (_bot_name, _channel_id, _channel_access_token, _channel_secret, _liff_id, _owner_id) 都必須提供';
    END IF;
    SELECT
        fs_insert_class(2, 3, '', '用戶創建的機器人', _owner_id) INTO new_class_id;
    INSERT INTO objects(chinese_name, owner_id)
        VALUES (_bot_name, _owner_id)
    RETURNING
        objects.object_id INTO object_id;
    INSERT INTO bot_details(object_id, channel_id, channel_access_token, channel_secret, liff_id)
        VALUES (object_id, _channel_id, _channel_access_token, _channel_secret, _liff_id)
    RETURNING
        bot_details.bot_detail_id INTO bot_detail_id;
    INSERT INTO class_object_relations(class_id, object_id)
        VALUES (new_class_id, object_id);
    PERFORM
        fs_insert_class(new_class_id, 4, '指令', '自動回覆指令', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 5, '設定', '跟Module功能有關的設定', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 6, '訊息紀錄', '訊息紀錄', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 7, '產品', '電商功能的產品', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 8, '知識', '問答功能的知識', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 9, '訂單', '電商功能的訂單', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 10, '預約', '預約功能的預約', _owner_id);
    PERFORM
        fs_insert_class(new_class_id, 11, '搜尋', '搜尋功能的資料', _owner_id);
    CALL sp_rename_class(new_class_id, CAST(object_id AS text));
    RETURN QUERY
    SELECT
        bot_detail_id,
        new_class_id,
        object_id,
        _bot_name,
        _channel_access_token,
        _liff_id,
        _owner_id;
END;
$$
LANGUAGE plpgsql;

