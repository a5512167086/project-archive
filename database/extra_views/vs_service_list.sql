CREATE OR REPLACE VIEW vs_service_list AS
SELECT sd.service_id,
    o.object_id,
    co.class_id,
    o.chinese_name AS service_name,
    o.chinese_description AS service_description,
    sd.duration_minutes,
    sd.price,
    sd.is_active,
    sd.created_at,
    sd.updated_at
FROM objects o
    JOIN service_details sd ON o.object_id = sd.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id;