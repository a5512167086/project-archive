CREATE TABLE IF NOT EXISTS order_details (
    order_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    total_amount INT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'confirmed', 'cancelled', 'completed')
    ),
    payment_method TEXT CHECK (
        payment_method IN ('cash', 'bank_transfer')
    ),
    payment_status TEXT CHECK (
        payment_status IN ('unpaid', 'paid', 'refunded')
    ),
    shipping_method TEXT CHECK (
        shipping_method IN ('home_delivery', 'store_pickup')
    ),
    shipping_fee INT DEFAULT 0 NOT NULL,
    tracking_number VARCHAR(128),
    recipient_name VARCHAR(128),
    recipient_phone VARCHAR(32),
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_details_object_id ON order_details(object_id);