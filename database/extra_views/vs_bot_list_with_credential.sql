CREATE OR REPLACE VIEW vs_bot_list_with_credential AS
SELECT
    bd.bot_detail_id,
    co.class_id,
    o.object_id,
    o.chinese_name,
    bd.channel_id,
    bd.channel_access_token,
    bd.channel_secret,
    o.owner_id
FROM
    objects o
    JOIN bot_details bd ON o.object_id = bd.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
