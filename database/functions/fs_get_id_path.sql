CREATE
OR REPLACE FUNCTION fs_getIDPath(PCID INT, CID INT) RETURNS VARCHAR(900) AS $ $ DECLARE nLevel INT;

IDPath VARCHAR(900);

BEGIN -- 獲取父節點的 nLevel
SELECT
    nLevel INTO nLevel
FROM
    Class
WHERE
    CID = PCID;

-- 判斷 nLevel 是否為 0
IF nLevel = 0 THEN IDPath := CAST(CID AS VARCHAR);

ELSE -- 構建 IDPath
SELECT
    IDPath || '/' || CAST(CID AS VARCHAR) INTO IDPath
FROM
    Class
WHERE
    CID = PCID;

END IF;

-- 返回 IDPath
RETURN IDPath;

END;

$ $ LANGUAGE plpgsql;