CREATE TABLE IF NOT EXISTS knowledge_files (
    file_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    object_id INT NOT NULL REFERENCES objects(object_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    display_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_knowledge_files_filename UNIQUE (filename),
    CONSTRAINT ck_knowledge_files_type CHECK (file_type IN ('pdf'))
);

CREATE INDEX IF NOT EXISTS idx_knowledge_files_object_created ON knowledge_files(object_id, created_at);