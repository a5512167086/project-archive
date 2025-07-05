CREATE OR REPLACE VIEW vs_category_list AS
SELECT i.parent_class_id,
    c.class_id,
    c.entity_id,
    c.chinese_name as category_name,
    c.chinese_description as category_description,
    c.created_at,
    c.updated_at
FROM inheritances i
    JOIN classes c ON i.child_class_id = c.class_id
    JOIN entities e ON c.entity_id = e.entity_id
WHERE c.entity_id = (
        SELECT entity_id
        FROM entities
        WHERE chinese_name = '類別'
        LIMIT 1
    );