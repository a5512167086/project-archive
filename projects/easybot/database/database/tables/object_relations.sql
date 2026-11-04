CREATE TABLE IF NOT EXISTS object_relations(
    first_object_id INT NOT NULL,
    second_object_id INT NOT NULL,
    rank INT,
    relation_description VARCHAR(900),
    PRIMARY KEY (first_object_id, second_object_id)
);

