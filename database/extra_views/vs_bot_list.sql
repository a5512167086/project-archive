CREATE OR REPLACE VIEW vs_bot_list AS
SELECT
    co.class_id,
    o.object_id,
    o.chinese_name,
    bd.channel_id,
    o.owner_id
FROM
    objects o
    JOIN bot_details bd ON o.object_id = bd.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
