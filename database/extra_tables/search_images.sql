CREATE TABLE IF NOT EXISTS search_images(
    search_image_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    image_src varchar NOT NULL,
    ocr_text varchar NOT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_search_images_object_id ON search_images(object_id);

