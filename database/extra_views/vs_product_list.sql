CREATE OR REPLACE VIEW vs_product_list AS
SELECT pd.product_id,
    o.object_id,
    o.chinese_name AS product_name,
    o.chinese_description AS product_description,
    co.class_id as category_id,
    pd.brand_id,
    pd.sku_code,
    pd.price,
    pd.stock,
    pd.is_active,
    pd.created_at,
    pd.updated_at
FROM objects o
    JOIN product_details pd ON o.object_id = pd.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id;