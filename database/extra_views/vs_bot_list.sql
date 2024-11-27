CREATE OR REPLACE VIEW vs_bot_list AS
SELECT
    o.object_id,
    o.chinese_name,
    bd.channel_id,
    bd.channel_access_token,
    bd.channel_secret,
    o.owner_id
FROM
    objects o
    JOIN bot_details bd ON o.object_id = bd.object_id;

