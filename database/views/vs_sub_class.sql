CREATE OR REPLACE VIEW vs_sub_class AS
SELECT i.parent_class_id,
    i.rank,
    c.class_id,
    c.entity_id,
    c.chinese_name,
    c.chinese_description,
    c.created_at,
    c.updated_at,
    c.subobject_count,
    c.click_count,
    c.keywords,
    c.owner_id,
    c.is_hided,
    c.is_deleted
FROM inheritances i
    JOIN classes c ON i.child_class_id = c.class_id;