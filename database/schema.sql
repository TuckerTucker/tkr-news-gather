-- Supabase Database Schema for TKR News Gatherer

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- News Sessions Table
CREATE TABLE news_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  province VARCHAR(50) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for province queries
CREATE INDEX idx_news_sessions_province ON news_sessions(province);
CREATE INDEX idx_news_sessions_created_at ON news_sessions(created_at DESC);

-- Articles Table
CREATE TABLE articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES news_sessions(id) ON DELETE CASCADE,
  wtkr_id VARCHAR(50) UNIQUE NOT NULL,
  article_id VARCHAR(255),
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  source_name VARCHAR(255),
  content TEXT,
  summary TEXT,
  pub_date TIMESTAMP WITH TIME ZONE,
  scraped_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX idx_articles_session_id ON articles(session_id);
CREATE INDEX idx_articles_wtkr_id ON articles(wtkr_id);
CREATE INDEX idx_articles_pub_date ON articles(pub_date DESC);
CREATE INDEX idx_articles_created_at ON articles(created_at DESC);

-- Processed Articles Table
CREATE TABLE processed_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  host_type VARCHAR(50) NOT NULL CHECK (host_type IN ('anchor', 'friend', 'newsreel')),
  processed_content TEXT NOT NULL,
  processing_metadata JSONB DEFAULT '{}'::jsonb,
  processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_processed_articles_article_id ON processed_articles(article_id);
CREATE INDEX idx_processed_articles_host_type ON processed_articles(host_type);

-- Audio Files Table
CREATE TABLE audio_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  processed_article_id UUID REFERENCES processed_articles(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  file_size INTEGER,
  duration_seconds FLOAT,
  voice_id VARCHAR(100),
  voice_settings JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_audio_files_processed_article_id ON audio_files(processed_article_id);
CREATE INDEX idx_audio_files_created_at ON audio_files(created_at DESC);

-- Create a view for easy querying
CREATE VIEW news_with_audio AS
SELECT 
  ns.id as session_id,
  ns.province,
  ns.created_at as session_date,
  a.id as article_id,
  a.wtkr_id,
  a.title,
  a.url,
  a.source_name,
  a.summary,
  a.pub_date,
  pa.id as processed_id,
  pa.host_type,
  pa.processed_content,
  af.id as audio_id,
  af.file_path,
  af.duration_seconds,
  af.voice_id
FROM news_sessions ns
JOIN articles a ON a.session_id = ns.id
LEFT JOIN processed_articles pa ON pa.article_id = a.id
LEFT JOIN audio_files af ON af.processed_article_id = pa.id
ORDER BY ns.created_at DESC, a.pub_date DESC;

-- Enable RLS on all tables
ALTER TABLE news_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_files ENABLE ROW LEVEL SECURITY;

-- For now, allow public read access (adjust based on your auth needs)
-- News Sessions - Public read
CREATE POLICY "Public can view news sessions" ON news_sessions
  FOR SELECT USING (true);

-- Articles - Public read
CREATE POLICY "Public can view articles" ON articles
  FOR SELECT USING (true);

-- Processed Articles - Public read
CREATE POLICY "Public can view processed articles" ON processed_articles
  FOR SELECT USING (true);

-- Audio Files - Public read
CREATE POLICY "Public can view audio files" ON audio_files
  FOR SELECT USING (true);

-- Service role has full access (for your backend)
CREATE POLICY "Service role has full access to news_sessions" ON news_sessions
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to articles" ON articles
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to processed_articles" ON processed_articles
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to audio_files" ON audio_files
  FOR ALL USING (auth.role() = 'service_role');

-- Function to get latest news session for a province
CREATE OR REPLACE FUNCTION get_latest_session(p_province VARCHAR)
RETURNS TABLE (
  id UUID,
  province VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE,
  article_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ns.id,
    ns.province,
    ns.created_at,
    COUNT(a.id) as article_count
  FROM news_sessions ns
  LEFT JOIN articles a ON a.session_id = ns.id
  WHERE ns.province = p_province
  GROUP BY ns.id
  ORDER BY ns.created_at DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old audio files
CREATE OR REPLACE FUNCTION cleanup_old_audio(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM audio_files
  WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep
  RETURNING COUNT(*) INTO deleted_count;
  
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Auto-update processed_at timestamp
CREATE OR REPLACE FUNCTION update_processed_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.processed_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_processed_articles_processed_at
  BEFORE UPDATE ON processed_articles
  FOR EACH ROW
  EXECUTE FUNCTION update_processed_at();