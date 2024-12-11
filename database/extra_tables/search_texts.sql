CREATE TABLE IF NOT EXISTS search_texts(
    search_text_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    type varchar,
    description varchar,
    price varchar,
    instruction varchar,
    ingredient varchar,
    url varchar,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_search_texts_object_id ON search_texts(object_id);

