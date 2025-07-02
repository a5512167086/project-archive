CREATE OR REPLACE VIEW vs_reservation_list AS
SELECT cor.class_id,
    rd.reservation_id,
    rd.object_id,
    rd.service_id,
    rd.price,
    o_service.chinese_name AS service_name,
    rd.notes,
    rd.reservation_date,
    rd.start_time,
    rd.end_time,
    rd.status,
    rd.payment_method,
    rd.payment_status,
    rd.created_at,
    rd.updated_at
FROM reservation_details rd
    JOIN service_details sd ON rd.service_id = sd.service_id
    JOIN objects o_service ON sd.object_id = o_service.object_id
    JOIN class_object_relations cor ON rd.object_id = cor.object_id;