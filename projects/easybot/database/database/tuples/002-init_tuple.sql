DO $$
DECLARE _entity_id INT;

BEGIN -- 取得 entity_id
SELECT entity_id INTO _entity_id
FROM entities
WHERE chinese_name = '資源'
LIMIT 1;

-- 插入根目錄 class（如果尚未存在）
INSERT INTO classes(
        entity_id,
        chinese_name,
        chinese_description,
        english_name,
        english_description,
        id_path,
        name_path,
        hierarchy_level
    )
SELECT _entity_id,
    '根目錄',
    '初始的根目錄',
    'Root',
    'Initial root',
    '1',
    '根目錄',
    1
WHERE NOT EXISTS (
        SELECT 1
        FROM classes
        WHERE entity_id = _entity_id
            AND chinese_name = '根目錄'
    );

END $$ LANGUAGE plpgsql;