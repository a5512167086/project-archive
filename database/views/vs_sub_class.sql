CREATE
OR REPLACE VIEW vs_SubClass AS
SELECT
    i.PCID AS CID,
    i.Rank,
    c.CID AS CCID,
    c.Type,
    c.CName,
    c.CDes,
    c.Since,
    c.LastModifiedDT,
    c.nObject,
    c.nClick,
    c.Keywords,
    c.OwnerMID,
    c.bHided,
    c.bDel
FROM
    Inheritance i
    JOIN Class c ON i.CCID = c.CID;