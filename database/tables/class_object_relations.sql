CREATE TABLE IF NOT EXISTS class_object_relations(
    class_id INT NOT NULL,
    object_id INT NOT NULL,
    rank SMALLINT,
    membership_grade SMALLINT,
    relation_description VARCHAR(900),
    PRIMARY KEY (class_id, object_id)
);

