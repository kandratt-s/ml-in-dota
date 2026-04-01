CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users.refresh_tokens (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id UUID NOT NULL,
	token_hash VARCHAR(64) NOT NULL UNIQUE,
	jti VARCHAR(36) NOT NULL UNIQUE,
	expires_at TIMESTAMPTZ NOT NULL,
	revoked BOOLEAN NOT NULL DEFAULT FALSE,
	fingerprint VARCHAR(64),
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	CONSTRAINT fk_refresh_tokens_user
		FOREIGN KEY (user_id)
		REFERENCES users.users(id)
		ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON users.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_jti ON users.refresh_tokens(jti);