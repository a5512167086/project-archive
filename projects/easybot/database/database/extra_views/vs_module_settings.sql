CREATE OR REPLACE VIEW vs_module_settings AS
SELECT
    ms.module_id,
    co.class_id,
    o.object_id,
    o.chinese_name,
    ms.is_enabled,
    ms.version,
    ms.description
FROM
    objects o
    JOIN module_settings ms ON o.object_id = ms.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
