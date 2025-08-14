CREATE TABLE IF NOT EXISTS order_items (
    order_item_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    product_id UUID NOT NULL,
    variant_id UUID,
    quantity INT NOT NULL,
    unit_price INT NOT NULL,
    subtotal INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_items_object_id ON order_items(object_id);

CREATE INDEX IF NOT EXISTS idx_order_items_variant_id ON order_items(variant_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);