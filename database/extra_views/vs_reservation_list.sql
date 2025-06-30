CREATE OR REPLACE VIEW vs_reservation_list AS
SELECT cor.class_id,
    rd.reservation_id,
    rd.object_id,
    rd.reservation_item_id,
    rd.price,
    o_item.chinese_name AS service_name,
    rd.notes,
    rd.reservation_date,
    rd.start_time,
    rd.end_time,
    rd.status,
    rd.payment_method,
    rd.payment_status,
    rd.created_at
FROM reservation_details rd
    JOIN reservation_item_details rid ON rd.reservation_item_id = rid.reservation_item_id
    JOIN objects o_item ON rid.object_id = o_item.object_id
    JOIN class_object_relations cor ON rd.object_id = cor.object_id;