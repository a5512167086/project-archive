CREATE OR REPLACE FUNCTION sp_insert_user(
        account VARCHAR(100),
        password VARCHAR(256),
        username VARCHAR(50),
        email VARCHAR(256),
        gender BOOLEAN,
        birthday DATE,
        phone_number VARCHAR(100),
        address VARCHAR(256),
        OUT new_user_id SMALLINT
    ) RETURNS SMALLINT AS $$
DECLARE hashed_pwd VARCHAR(512);
valid INT := 1;
-- 假設帳號預設為有效
status INT := 0;
-- 帳號初始狀態設為非活躍
verify_code VARCHAR(512);
new_object_id SMALLINT;
BEGIN -- 檢查 account 是否已經存在
IF (
    SELECT COUNT(*)
    FROM users
    WHERE account = TRIM(account)
) > 0 THEN RAISE EXCEPTION 'Error: Account已存在，不可再新增';
END IF;
-- 計算 password 和 verify_code
hashed_pwd := encode(digest(TRIM(password), 'sha512'), 'hex');
verify_code := encode(digest(account || hashed_pwd, 'sha512'), 'hex');
-- 插入新 object，獲取新生成的 object_id
INSERT INTO objects (entity_id, chinese_name)
VALUES (2, username)
RETURNING object_id INTO new_object_id;
-- 插入新 user
INSERT INTO users (
        user_id,
        account,
        password,
        is_valid,
        status,
        email_verify_code,
        email,
        gender,
        birthday,
        address,
        phone_number
    )
VALUES (
        new_object_id,
        TRIM(account),
        hashed_pwd,
        valid,
        status,
        verify_code,
        TRIM(email),
        gender,
        birthday,
        TRIM(address),
        TRIM(phone_number)
    );
-- 設置返回的 user_id
new_user_id := new_object_id;
EXCEPTION
WHEN OTHERS THEN -- 捕捉錯誤並返回錯誤訊息
RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤行號：%',
SQLSTATE,
SQLERRM,
GETSTACKEDDIAGNOSTICS.LINE;
END;
$$ LANGUAGE plpgsql;