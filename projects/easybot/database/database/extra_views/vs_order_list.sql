CREATE OR REPLACE VIEW vs_order_list AS
SELECT co.class_id,
    od.order_id,
    o.object_id,
    od.total_amount,
    od.status,
    od.payment_method,
    od.payment_status,
    od.shipping_method,
    od.shipping_fee,
    od.tracking_number,
    od.recipient_name,
    od.recipient_phone,
    od.shipping_address,
    od.notes,
    od.created_at,
    od.updated_at
FROM objects o
    JOIN order_details od ON o.object_id = od.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id;