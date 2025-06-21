CREATE OR REPLACE PROCEDURE sp_delete_class(IN _class_id INT) LANGUAGE plpgsql AS $$
DECLARE error_message TEXT;

error_context TEXT;

orphan_group_id INT;

BEGIN -- 確認 class 是否存在
IF (
    SELECT COUNT(*)
    FROM classes
    WHERE class_id = _class_id
) = 1 THEN -- 找出與該 class 有關的 group_id
FOR orphan_group_id IN
SELECT DISTINCT group_id
FROM permissions
WHERE class_id = _class_id
    AND role_type = FALSE LOOP -- 刪除該 class 的權限
DELETE FROM permissions
WHERE class_id = _class_id;

-- 檢查該 group 是否還在其他 permissions 出現
IF NOT EXISTS (
    SELECT 1
    FROM permissions
    WHERE role_type = FALSE
        AND group_id = orphan_group_id
) THEN
DELETE FROM groups
WHERE group_id = orphan_group_id;

END IF;

END LOOP;

-- 刪除其他相關資料
DELETE FROM class_object_relations
WHERE class_id = _class_id;

DELETE FROM inheritances
WHERE child_class_id = _class_id
    OR parent_class_id = _class_id;

DELETE FROM classes
WHERE class_id = _class_id;

ELSE RAISE EXCEPTION 'Error: This class does not exist';

END IF;

EXCEPTION
WHEN OTHERS THEN GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
error_context = PG_EXCEPTION_CONTEXT;

RAISE EXCEPTION 'Error code: %, Error message: %, Context: %',
SQLSTATE,
error_message,
error_context;

END;

$$;