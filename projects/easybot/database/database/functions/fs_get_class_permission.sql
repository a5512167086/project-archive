CREATE OR REPLACE FUNCTION fs_get_class_permission(_class_id INT, _user_id INT)
    RETURNS TABLE(
        subscribe BOOLEAN,
        manage BOOLEAN,
        update_permission BOOLEAN,
        delete_permission BOOLEAN,
        insert_permission BOOLEAN,
        read_permission BOOLEAN,
        view_permission BOOLEAN
    )
    AS $$
BEGIN
    RETURN QUERY WITH permission_temp AS(
        -- 針對群組的權限
        SELECT
(permission.permission_bits & 64) > 0 AS subscribe,
(permission.permission_bits & 32) > 0 AS manage,
(permission.permission_bits & 16) > 0 AS update_permission,
(permission.permission_bits & 8) > 0 AS delete_permission,
(permission.permission_bits & 4) > 0 AS insert_permission,
(permission.permission_bits & 2) > 0 AS read_permission,
(permission.permission_bits & 1) > 0 AS view_permission
        FROM
            permission
            JOIN groups ON permission.role_id = groups.group_id
            JOIN group_members ON groups.group_id = group_members.group_id
        WHERE
            permission.class_id = class_id
            AND permission.role_type = FALSE
            AND groups.is_deleted = FALSE
            AND group_members.status = TRUE
            AND group_members.member_id = user_id
        UNION ALL
        -- 針對成員的權限
        SELECT
(permission.permission_bits & 64) > 0 AS subscribe,
(permission.permission_bits & 32) > 0 AS manage,
(permission.permission_bits & 16) > 0 AS update_permission,
(permission.permission_bits & 8) > 0 AS delete_permission,
(permission.permission_bits & 4) > 0 AS insert_permission,
(permission.permission_bits & 2) > 0 AS read_permission,
(permission.permission_bits & 1) > 0 AS view_permission
        FROM
            permission
            JOIN member ON permission.role_id = member.member_id
        WHERE
            permission.class_id = class_id
            AND permission.role_type = TRUE
            AND member.member_id = user_id
)
    SELECT
        MAX(subscribe) AS subscribe,
        MAX(manage) AS manage,
        MAX(update_permission) AS update_permission,
        MAX(delete_permission) AS delete_permission,
        MAX(insert_permission) AS insert_permission,
        MAX(read_permission) AS read_permission,
        MAX(view_permission) AS view_permission
    FROM
        permission_temp;
END;
$$
LANGUAGE plpgsql;

