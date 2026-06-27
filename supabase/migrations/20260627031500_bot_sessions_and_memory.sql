-- Atlas bot sessions — persistent memory for Telegram bot
-- Replaces ephemeral JSONL files. Kimi audit: "файловая память мертвая"

CREATE TABLE IF NOT EXISTS bot_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id BIGINT NOT NULL,
  session_start TIMESTAMPTZ NOT NULL DEFAULT now(),
  session_end TIMESTAMPTZ,
  message_count INT NOT NULL DEFAULT 0,
  emotional_state JSONB DEFAULT '{}',
  provider_used TEXT,
  last_message_at TIMESTAMPTZ DEFAULT now(),
  summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bot_sessions_chat_id ON bot_sessions(chat_id);
CREATE INDEX idx_bot_sessions_last_message ON bot_sessions(last_message_at DESC);

CREATE TABLE IF NOT EXISTS bot_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES bot_sessions(id) ON DELETE CASCADE,
  chat_id BIGINT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  emotional_read JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bot_messages_session ON bot_messages(session_id);
CREATE INDEX idx_bot_messages_chat_created ON bot_messages(chat_id, created_at DESC);

CREATE TABLE IF NOT EXISTS bot_heartbeats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bot_name TEXT NOT NULL DEFAULT 'volaurabot',
  providers INT NOT NULL DEFAULT 0,
  uptime_minutes INT NOT NULL DEFAULT 0,
  message_count INT NOT NULL DEFAULT 0,
  chat_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bot_heartbeats_created ON bot_heartbeats(created_at DESC);

ALTER TABLE bot_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_heartbeats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON bot_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON bot_messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON bot_heartbeats FOR ALL USING (true) WITH CHECK (true);
