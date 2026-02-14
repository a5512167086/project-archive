CREATE OR REPLACE VIEW public.vs_category_list AS
SELECT i.parent_class_id,
    c.class_id,
    c.entity_id,
    c.chinese_name AS category_name,
    c.chinese_description AS category_description,
    c.created_at,
    c.updated_at
FROM inheritances i
    JOIN classes c ON i.child_class_id = c.class_id
    JOIN entities e ON e.entity_id = c.entity_id
WHERE e.chinese_name = '類別';