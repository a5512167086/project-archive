CREATE TABLE IF NOT EXISTS groups (
    group_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    group_name VARCHAR(50) NOT NULL,
    group_description VARCHAR(1024),
    status SMALLINT,
    created_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    group_type SMALLINT,
    is_hidden BOOLEAN DEFAULT FALSE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    identifier INT,
    class_id INT,
    CONSTRAINT uq_groups UNIQUE (group_name)
);

