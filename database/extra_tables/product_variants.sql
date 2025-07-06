CREATE TABLE IF NOT EXISTS product_variants (
    variant_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT,
    variant_name VARCHAR(100) NOT NULL,
    sku_code VARCHAR(64) UNIQUE,
    price INT,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);