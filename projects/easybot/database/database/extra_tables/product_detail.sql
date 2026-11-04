CREATE TABLE IF NOT EXISTS product_details (
    product_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    brand_id INT,
    object_id int NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    sku_code VARCHAR(64) NULL,
    price INT NOT NULL,
    stock INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_details_object_id ON product_details(object_id);