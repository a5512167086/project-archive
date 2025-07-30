CREATE TABLE IF NOT EXISTS order_items (
    order_item_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    variant_id UUID,
    product_name_snapshot VARCHAR(512) NOT NULL,
    sku_snapshot VARCHAR(64) NOT NULL,
    price_snapshot INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY(object_id) REFERENCES objects(object_id),
    FOREIGN KEY(variant_id) REFERENCES product_variants(variant_id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_object_id ON order_items(object_id);

CREATE INDEX IF NOT EXISTS idx_order_items_variant_id ON order_items(variant_id);