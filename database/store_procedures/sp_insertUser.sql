CREATE
OR REPLACE FUNCTION xps_addNewMember(
    Account VARCHAR(100),
    Password VARCHAR(256),
    UserName VARCHAR(50),
    EMail VARCHAR(256),
    Sex BOOLEAN,
    Birthday DATE,
    Phone VARCHAR(100),
    Address VARCHAR(256),
    OUT NewMID INT
) RETURNS VOID AS $ $ DECLARE License VARCHAR(512);

PWD VARCHAR(512);

Valid INT;

Status INT;

VarifyCode VARCHAR(512);

NewOID INT;

BEGIN -- 檢查 Account 是否已經存在
IF (
    SELECT
        COUNT(*)
    FROM
        Member
    WHERE
        Account = TRIM(Account)
) > 0 THEN RAISE EXCEPTION 'Error: Account已存在，不可再新增';

END IF;

-- 獲取 License
SELECT
    Des INTO License
FROM
    SystemConfig
WHERE
    Name = 'License';

-- 計算 PWD 和 VarifyCode
PWD := encode(
    digest(TRIM(Password) || License, 'sha512'),
    'hex'
);

VarifyCode := encode(
    digest(Account || PWD || License, 'sha512'),
    'hex'
);

-- 插入新 Object，獲取新生成的 OID
INSERT INTO
    Object (Type, CName)
VALUES
    (2, UserName) RETURNING OID INTO NewOID;

-- 插入新 Member
INSERT INTO
    Member (
        MID,
        Account,
        PWD,
        Valid,
        Status,
        VerifyCode,
        EMail,
        Sex,
        Birthday,
        Address,
        Phone
    )
VALUES
    (
        NewOID,
        Account,
        PWD,
        Valid,
        Status,
        VarifyCode,
        EMail,
        Sex,
        Birthday,
        Address,
        Phone
    );

-- 插入 GM 表
INSERT INTO
    GM (GID, MID, Role, Type, Status)
VALUES
    (2, NewOID, 2, 1, 0);

-- 返回新生成的 Member ID
NewMID := NewOID;

EXCEPTION
WHEN OTHERS THEN -- 捕捉錯誤並返回錯誤訊息
RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤行號：%, 錯誤程序名稱：%',
SQLSTATE,
SQLERRM,
GETSTACKEDDIAGNOSTICS.LINE,
COALESCE(GETSTACKEDDIAGNOSTICS.PROCEDURE, '');

END;

$ $ LANGUAGE plpgsql;