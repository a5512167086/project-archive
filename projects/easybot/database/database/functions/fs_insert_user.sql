CREATE OR REPLACE FUNCTION fs_insert_user(_username TEXT, _email TEXT, _password TEXT)
    RETURNS UUID
    AS $$
DECLARE
    new_user_id UUID;
    error_message TEXT;
    error_context TEXT;
BEGIN
    -- Check if email already exists
    IF (
        SELECT
            COUNT(*)
        FROM
            users
        WHERE
            TRIM(email) = TRIM(_email)) > 0 THEN
        RAISE EXCEPTION 'Error: EMail已存在，不可再新增';
    END IF;
    -- Insert new user and return the new user ID
    INSERT INTO users(
        username,
        password,
        is_valid,
        status,
        email)
    VALUES (
        _username,
        _password,
        TRUE,
        1,
        _email)
RETURNING
    user_id INTO new_user_id;
    -- Return the newly created user ID
    RETURN new_user_id;
EXCEPTION
    WHEN OTHERS THEN
        -- Capture error details and raise the error with additional context
        GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
        error_context = PG_EXCEPTION_CONTEXT;
    RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤上下文：%', SQLSTATE, error_message, error_context;
END;

$$
LANGUAGE plpgsql;

