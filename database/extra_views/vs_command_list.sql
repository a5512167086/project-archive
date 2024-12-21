CREATE OR REPLACE VIEW vs_command_list AS
SELECT
    cd.command_detail_id,
    co.class_id,
    o.object_id,
    o.chinese_name,
    cd.command_keyword,
    cd.type
FROM
    objects o
    JOIN command_details cd ON o.object_id = cd.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
