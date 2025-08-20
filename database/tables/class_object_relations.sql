CREATE TABLE IF NOT EXISTS class_object_relations(
    class_id INT NOT NULL,
    object_id INT NOT NULL,
    rank SMALLINT,
    membership_grade SMALLINT,
    relation_description VARCHAR(900),
    PRIMARY KEY (class_id, object_id)
);

CREATE INDEX IF NOT EXISTS idx_class_object_relations_object_id ON class_object_relations(object_id);