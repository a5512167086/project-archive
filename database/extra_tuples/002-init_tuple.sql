DO $$
DECLARE _entity_id INT;

BEGIN
SELECT entity_id INTO _entity_id
FROM entities
WHERE chinese_name = '機器人'
LIMIT 1;

IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '機器人'
        AND entity_id = _entity_id
) THEN PERFORM fs_insert_class(1, _entity_id, '機器人', '機器人Class', NULL);

END IF;

END $$;