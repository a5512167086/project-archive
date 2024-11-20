CREATE OR REPLACE PROCEDURE sp_insert_bot(IN _bot_name VARCHAR(50), IN _channel_id VARCHAR(100), IN _channel_access_token VARCHAR(100), IN _channel_secret VARCHAR(100), IN _owner_id UUID)
LANGUAGE plpgsql
AS $$
DECLARE
    new_class_id INT;
    new_object_id INT;
BEGIN
    -- 驗證輸入參數是否為 NULL
    IF (_bot_name IS NULL OR _channel_id IS NULL OR _channel_access_token IS NULL OR _channel_secret IS NULL OR _owner_id IS NULL) THEN
        RAISE EXCEPTION 'Error: 所有參數 (_bot_name, _channel_id, _channel_access_token, _channel_secret, _owner_id) 都必須提供';
    END IF;
    -- 呼叫 fs_insert_class 並取得 new_class_id
    SELECT
        fs_insert_class(2, 3, '', '', _owner_id) INTO new_class_id;
    -- First insert into parent table (objects)
    INSERT INTO objects(
        chinese_name,
        owner_id)
    VALUES (
        _bot_name,
        _owner_id)
RETURNING
    object_id INTO new_object_id;
    -- Then insert additional fields into bot_details
    INSERT INTO bot_details(
        object_id,
        chinese_name,
        owner_id,
        channel_id,
        channel_access_token,
        channel_secret)
    VALUES (
        new_object_id,
        _bot_name,
        _owner_id,
        _channel_id,
        _channel_access_token,
        _channel_secret);
    -- 插入到 class_object_relations 表
    INSERT INTO class_object_relations(
        class_id,
        object_id)
    VALUES (
        new_class_id,
        new_object_id);
    -- 呼叫 sp_rename_class，傳遞 new_class_id 和 new_object_id
    CALL sp_rename_class(new_class_id, CAST(new_object_id AS TEXT));
END;
$$;

