CREATE OR REPLACE FUNCTION fs_check_user_permission(_class_id INT, _user_id INT, _bit_position SMALLINT)
    RETURNS BOOLEAN
    AS $$
DECLARE
    result BOOLEAN := FALSE;
    count_result INT;
    sum_result INT;
BEGIN
    -- 計算 Permission 表中符合條件的行數
    count_result :=(
        SELECT
            COUNT(*)
        FROM
            permission
        WHERE
            class_id = _class_id
            AND role_type = TRUE
            AND role_id = _user_id);
    IF count_result = 1 THEN
        -- 若找到一條符合條件的行，檢查該行的位元權限
        result :=(
            SELECT
                fs_check_bitwise(permission_bits, _bit_position)
            FROM
                permission
            WHERE
                class_id = _class_id
                AND role_type = TRUE
                AND role_id = _user_id);
    ELSE
        -- 若無符合條件的行，則計算關聯表的位元權限之和
        sum_result :=(
            SELECT
                SUM(
                    CASE WHEN fs_check_bitwise(p.permission_bits, _bit_position) THEN
                        1
                    ELSE
                        0
                    END)
            FROM
                permission p
                JOIN group_members gm ON p.role_id = gm.group_id
                JOIN groups g ON gm.group_id = g.group_id
            WHERE
                p.class_id = _class_id
                AND p.role_type = FALSE
                AND gm.member_id = _user_id
                AND g.is_deleted = FALSE);
        IF sum_result > 0 THEN
            result := TRUE;
        END IF;
    END IF;
    RETURN result;
END;
$$
LANGUAGE plpgsql;

