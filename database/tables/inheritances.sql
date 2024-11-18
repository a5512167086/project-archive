CREATE TABLE IF NOT EXISTS inheritances(
    parent_class_id INT NOT NULL,
    child_class_id INT NOT NULL,
    rank SMALLINT,
    membership_grade SMALLINT,
    PRIMARY KEY (parent_class_id, child_class_id)
);

