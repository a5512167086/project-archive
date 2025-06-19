DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM groups
    WHERE group_name = 'Administrators'
) THEN
INSERT INTO groups (group_name, group_description)
VALUES ('Administrators', 'System Administrator Group');

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM groups
    WHERE group_name = 'Employees'
) THEN
INSERT INTO groups (group_name, group_description)
VALUES ('Managers', 'System Manager Group');

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM groups
    WHERE group_name = 'Users'
) THEN
INSERT INTO groups (group_name, group_description)
VALUES ('Users', 'System User Group');

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM groups
    WHERE group_name = 'Guests'
) THEN
INSERT INTO groups (group_name, group_description)
VALUES ('Guests', 'System Guest Group');

END IF;

END $$;