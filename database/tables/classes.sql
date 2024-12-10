CREATE TABLE IF NOT EXISTS classes(
    class_id int GENERATED ALWAYS AS IDENTITY,
    entity_id int,
    chinese_name varchar(256) NOT NULL,
    chinese_description varchar(4000),
    english_name varchar(256),
    english_description varchar(4000),
    id_path varchar(900),
    name_path varchar(450),
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    subobject_count int DEFAULT 0 NOT NULL,
    class_rank smallint DEFAULT 0,
    object_rank smallint DEFAULT 0,
    hierarchy_level smallint,
    click_count int DEFAULT 0 NOT NULL,
    keywords varchar(512) DEFAULT '',
    owner_id uuid DEFAULT NULL,
    is_hided boolean DEFAULT FALSE,
    is_deleted boolean DEFAULT FALSE,
    PRIMARY KEY (class_id),
    CONSTRAINT uq_classes_id_path UNIQUE (id_path),
    CONSTRAINT uq_classes_name_path UNIQUE (name_path)
);

CREATE INDEX IF NOT EXISTS ix_classes_entity_id ON classes(entity_id);

