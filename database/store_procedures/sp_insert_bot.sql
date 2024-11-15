CREATE OR REPLACE PROCEDURE sp_insert_bot(IN _bot_name varchar(50), IN _channel_id varchar(100), IN _channel_access_token varchar(100), IN _channel_secret varchar(100), IN _owner_id varchar(100))
LANGUAGE plpgsql
AS $$
BEGIN
    IF(_chinese_name IS NULL OR _english_name IS NULL OR _is_relational IS NULL) THEN
        RAISE EXCEPTION 'Error: 所有參數 (_bot_name, _channel_id, _channel_access_token, _channel_secret, _owner_id) 都必須提供';
    END IF;
    SELECT
        fs_insert_class(2, 3, NULL, NULL, _owner_id);
END;
$$;

