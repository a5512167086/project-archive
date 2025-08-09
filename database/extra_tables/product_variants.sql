CREATE TABLE IF NOT EXISTS product_variants (
    variant_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT,
    variant_name VARCHAR(100) NOT NULL,
    sku_code VARCHAR(64),
    price INT,
    stock INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_variants_object_id ON product_variants(object_id);