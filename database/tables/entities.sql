CREATE TABLE IF NOT EXISTS entities (
    entity_id SMALLINT GENERATED ALWAYS AS IDENTITY,
    chinese_name VARCHAR(50) NOT NULL,
    english_name VARCHAR(50) NOT NULL,
    is_relational BOOLEAN DEFAULT TRUE NOT NULL,
    is_hidable BOOLEAN DEFAULT FALSE,
    is_deletable BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (entity_id)
);