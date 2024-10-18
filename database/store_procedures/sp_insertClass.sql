CREATE
OR REPLACE FUNCTION xp_insertClass(
    PCID INT,
    -- 父節點
    Type INT,
    -- 節點類型
    CName VARCHAR(255),
    -- 節點名稱
    CDes VARCHAR(4000),
    -- 節點描述
    OwnerMID INT,
    -- 所有者ID
    OUT NewCID INT -- 新節點ID，回傳
) RETURNS VOID AS $ $ DECLARE _PCID INT;

_PNamePath VARCHAR(900);

_NewNamePath VARCHAR(900);

_NewCID INT;

_NewLevel INT;

BEGIN -- 初始化返回值
NewCID := NULL;

-- 查詢父節點的 CID 和 NamePath
SELECT
    CID,
    NamePath INTO _PCID,
    _PNamePath
FROM
    Class
WHERE
    CID = PCID;

IF _PCID IS NOT NULL THEN -- 獲取新節點的 NamePath
_NewNamePath := fs_getNamePath(PCID, CName);

-- 檢查 NamePath 是否已存在
IF (
    SELECT
        COUNT(*)
    FROM
        Class
    WHERE
        NamePath = _NewNamePath
) = 0 THEN -- 插入新節點到 Class 表
INSERT INTO
    Class (CName, Type, CDes)
VALUES
    (CName, Type, CDes) RETURNING CID INTO _NewCID;

-- 插入繼承關係
INSERT INTO
    Inheritance (PCID, CCID)
VALUES
    (PCID, _NewCID);

-- 從父節點繼承權限
INSERT INTO
    Permission (CID, RoleType, RoleID, PermissionBits)
SELECT
    _NewCID,
    RoleType,
    RoleID,
    PermissionBits
FROM
    Permission
WHERE
    CID = PCID;

-- 計算新節點的層級
SELECT
    nLevel + 1 INTO _NewLevel
FROM
    Class
WHERE
    CID = PCID;

-- 更新新節點的屬性
UPDATE
    Class
SET
    nLevel = _NewLevel,
    NamePath = _NewNamePath,
    IDPath = fs_getIDPath(PCID, _NewCID)
WHERE
    CID = _NewCID;

-- 設置返回的新節點ID
NewCID := _NewCID;

ELSE -- 節點已存在，拋出錯誤
RAISE EXCEPTION 'Error: 節點已存在，不得再新增';

END IF;

ELSE -- 父節點不存在，拋出錯誤
RAISE EXCEPTION 'Error: 沒有PCID';

END IF;

EXCEPTION
WHEN OTHERS THEN -- 捕獲錯誤並返回錯誤訊息
RAISE EXCEPTION USING MESSAGE = '錯誤訊息：' || SQLERRM,
DETAIL = '錯誤行號：' || GETSTACKEDDIAGNOSTICS.LINE;

END;

$ $ LANGUAGE plpgsql;