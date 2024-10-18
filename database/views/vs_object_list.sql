CREATE
OR REPLACE VIEW vs_ObjectList AS
SELECT
    co.CID,
    co.Rank,
    o.OID,
    o.Type,
    o.CName,
    o.Since,
    o.LastModifiedDT,
    o.OwnerMID,
    o.nClick,
    o.bHided,
    o.bDel
FROM
    CO
    JOIN Object o ON co.OID = o.OID;