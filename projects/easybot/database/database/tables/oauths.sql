CREATE TABLE IF NOT EXISTS oauths(
    user_id UUID,
    oauth_provider VARCHAR(300),
    oauth_user_id VARCHAR(100),
    CONSTRAINT uq_oauths_provider_user UNIQUE (oauth_provider, oauth_user_id)
);