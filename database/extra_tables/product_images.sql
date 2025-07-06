CREATE TABLE IF NOT EXISTS product_images (
    image_id SERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    object_id int NOT NULL,
    display_order SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_product_images_object_id ON product_images(object_id);