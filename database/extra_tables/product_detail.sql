DROP TABLE IF EXISTS products_details;

CREATE TABLE products_details (
    product_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    brand_id INT,
    object_id int NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_details_object_id ON products_details(object_id);