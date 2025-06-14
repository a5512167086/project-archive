CREATE OR REPLACE VIEW vs_reservation_item_list AS
SELECT o.object_id,
    co.class_id,
    o.chinese_name AS reservation_name,
    o.chinese_description AS reservation_description,
    rd.duration_minutes,
    rd.price,
    rd.is_active AS item_is_active,
    rd.created_at AS item_created_at,
    rd.updated_at AS item_updated_at
FROM objects o
    JOIN reservation_item_details rd ON o.object_id = rd.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id;