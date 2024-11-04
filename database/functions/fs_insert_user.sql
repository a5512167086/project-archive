CREATE OR REPLACE FUNCTION fs_insert_user(
        _username TEXT,
        _password TEXT,
        _email TEXT,
        _gender BOOLEAN,
        _birthday DATE,
        _phone_number VARCHAR(100),
        _address VARCHAR(256)
    ) RETURNS INT AS $$
DECLARE new_user_id INT;
new_object_id INT;
error_message TEXT;
error_context TEXT;
BEGIN -- Check if email already exists
IF (
    SELECT COUNT(*)
    FROM users
    WHERE TRIM(email) = TRIM(_email)
) > 0 THEN RAISE EXCEPTION 'Error: EMail已存在，不可再新增';
END IF;
-- Insert new object into objects table
INSERT INTO objects (entity_id, chinese_name)
VALUES (2, _username)
RETURNING object_id INTO new_object_id;
-- Insert new user and return the new user id
INSERT INTO users (
        user_id,
        password,
        is_valid,
        status,
        email,
        gender,
        birthday,
        address,
        phone_number
    )
VALUES (
        new_object_id,
        _password,
        TRUE,
        1,
        _email,
        _gender,
        _birthday,
        _address,
        _phone_number
    )
RETURNING user_id INTO new_user_id;
-- Return the newly created user ID
RETURN new_user_id;
EXCEPTION
WHEN OTHERS THEN -- Capture error details and raise the error with additional context
GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
error_context = PG_EXCEPTION_CONTEXT;
RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤上下文：%',
SQLSTATE,
error_message,
error_context;
END;
$$ LANGUAGE plpgsql;