CREATE OR REPLACE PROCEDURE sp_insert_bot(IN _bot_name VARCHAR(50), IN _channel_id VARCHAR(100), IN _channel_access_token VARCHAR(100), IN _channel_secret VARCHAR(100), IN _owner_id UUID)
LANGUAGE plpgsql
AS $$
DECLARE
    new_class_id INT;
    new_object_id INT;
BEGIN
    IF (_bot_name IS NULL OR _channel_id IS NULL OR _channel_access_token IS NULL OR _channel_secret IS NULL OR _owner_id IS NULL) THEN
        RAISE EXCEPTION 'Error: 所有參數 (_bot_name, _channel_id, _channel_access_token, _channel_secret, _owner_id) 都必須提供';
    END IF;
    -- 使用 SELECT INTO 將返回值存入 new_class_id
    SELECT
        fs_insert_class(2, 3, 'tmp', '', _owner_id) INTO new_class_id;
    -- 你可以在這裡使用 new_class_id 做進一步的處理，例如插入到其他表中或進行其他邏輯操作
    SELECT
        fs_insert_object(new_class_id, NULL, _bot_name, '', _owner_id) INTO new_object_id;
    UPDATE
        classes
    SET
        chinese_name = new_object_id
    WHERE
        class_id = new_class_id;
    INSERT INTO bot_details(
        object_id,
        channel_id,
        channel_access_token,
        channel_secret)
    VALUES (
        new_object_id,
        _channel_id,
        _channel_access_token,
        _channel_secret);
END;
$$;

