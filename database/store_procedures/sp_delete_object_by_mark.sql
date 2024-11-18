CREATE OR REPLACE PROCEDURE sp_delete_object_by_mark(_object_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    object_count INT;
    error_message TEXT;
    error_context TEXT;
BEGIN
    -- Check if the object exists
    SELECT
        COUNT(*) INTO object_count
    FROM
        objects
    WHERE
        object_id = _object_id;
    IF object_count = 1 THEN
        -- Mark object as deleted and update last modified date
        UPDATE
            objects
        SET
            is_deleted = TRUE,
            updated_at = NOW()
        WHERE
            object_id = _object_id;
    ELSE
        -- Raise an exception if the object does not exist
        RAISE EXCEPTION 'Error: 此 Object 不存在';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- Capture error details and raise the error with additional context
        GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
        error_context = PG_EXCEPTION_CONTEXT;
    RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤上下文：%', SQLSTATE, error_message, error_context;
END;

$$;

