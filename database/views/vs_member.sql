CREATE
OR REPLACE VIEW vs_Member AS
SELECT
    o.OID,
    o.Type,
    o.CName,
    o.CDes,
    o.EName,
    o.EDes,
    m.Account,
    m.PWD,
    m.Valid,
    m.Status,
    m.VerifyCode,
    m.EMail,
    m.Phone,
    m.Address,
    m.Birthday,
    m.Nation,
    m.ClassID,
    m.SendEMailOK,
    m.LastLoginDT,
    m.LoginCount,
    m.LoginErrCount,
    o.Since,
    o.LastModifiedDT,
    o.bHided,
    o.bDel
FROM
    Member m
    JOIN Object o ON m.MID = o.OID;