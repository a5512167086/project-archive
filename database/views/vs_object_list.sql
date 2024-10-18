CREATE OR REPLACE VIEW vs_object_list AS
SELECT cor.class_id,
    cor.rank,
    o.object_id,
    o.entity_id,
    o.chinese_name,
    o.created_at,
    o.updated_at,
    o.owner_id,
    o.click_count,
    o.is_hided,
    o.is_deleted
FROM class_object_relations cor
    JOIN objects o ON cor.object_id = o.object_id;