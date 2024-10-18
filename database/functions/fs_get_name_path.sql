CREATE
OR REPLACE FUNCTION fs_getNamePath(PCID INT, CName VARCHAR(255)) RETURNS VARCHAR(900) AS $ $ DECLARE nLevel INT;

NamePath VARCHAR(900);

BEGIN -- 查詢父節點的 nLevel
SELECT
    nLevel INTO nLevel
FROM
    Class
WHERE
    CID = PCID;

-- 根據 nLevel 判斷生成 NamePath
IF nLevel = 0 THEN NamePath := CName;

ELSE
SELECT
    NamePath || '/' || CName INTO NamePath
FROM
    Class
WHERE
    CID = PCID;

END IF;

-- 返回 NamePath
RETURN NamePath;

END;

$ $ LANGUAGE plpgsql;