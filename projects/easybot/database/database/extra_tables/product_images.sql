CREATE TABLE IF NOT EXISTS product_images (
    image_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    object_id INT NOT NULL REFERENCES objects(object_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_product_images_filename UNIQUE (object_id, filename)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_images_primary ON product_images(object_id)
WHERE is_primary;

CREATE INDEX IF NOT EXISTS idx_product_images_object_created_at ON product_images(object_id, created_at);