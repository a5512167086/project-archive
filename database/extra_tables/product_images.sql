CREATE TABLE IF NOT EXISTS product_images (
    image_id SERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    object_id int NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_product_images_object_id ON product_images(object_id);