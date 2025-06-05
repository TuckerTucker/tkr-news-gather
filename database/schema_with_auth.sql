-- Complete Supabase Database Schema for TKR News Gatherer
-- Includes news functionality + authentication system
-- Use this for NEW projects, or use auth_migration.sql for existing ones

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================================================
-- AUTHENTICATION TABLES
-- ==================================================

-- User profiles table to extend Supabase auth.users
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  email VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'editor', 'admin')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user profiles
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);

-- Enable RLS on user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- User audit log for tracking actions
CREATE TABLE user_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,
  table_name VARCHAR(100),
  record_id UUID,
  details JSONB DEFAULT '{}'::jsonb,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit log
CREATE INDEX idx_user_audit_log_user_id ON user_audit_log(user_id);
CREATE INDEX idx_user_audit_log_action ON user_audit_log(action);
CREATE INDEX idx_user_audit_log_created_at ON user_audit_log(created_at DESC);

-- Enable RLS on audit log
ALTER TABLE user_audit_log ENABLE ROW LEVEL SECURITY;

-- ==================================================
-- NEWS CONTENT TABLES
-- ==================================================

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

-- ==================================================
-- ENABLE ROW LEVEL SECURITY ON ALL TABLES
-- ==================================================

ALTER TABLE news_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_files ENABLE ROW LEVEL SECURITY;

-- ==================================================
-- ROW LEVEL SECURITY POLICIES - USER PROFILES
-- ==================================================

-- User profile policies
CREATE POLICY "Users can view their own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all profiles" ON user_profiles
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Admins can view all profiles" ON user_profiles
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role = 'admin'
    )
  );

-- ==================================================
-- ROW LEVEL SECURITY POLICIES - NEWS CONTENT
-- ==================================================

-- News Sessions - Require authentication for read, write permissions based on role
CREATE POLICY "Authenticated users can view news sessions" ON news_sessions
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Editors and admins can insert news sessions" ON news_sessions
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Editors and admins can update news sessions" ON news_sessions
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Admins can delete news sessions" ON news_sessions
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role = 'admin'
    )
  );

-- Articles - Similar pattern
CREATE POLICY "Authenticated users can view articles" ON articles
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Editors and admins can insert articles" ON articles
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Editors and admins can update articles" ON articles
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Admins can delete articles" ON articles
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role = 'admin'
    )
  );

-- Processed Articles - Similar pattern
CREATE POLICY "Authenticated users can view processed articles" ON processed_articles
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Editors and admins can insert processed articles" ON processed_articles
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Editors and admins can update processed articles" ON processed_articles
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Admins can delete processed articles" ON processed_articles
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role = 'admin'
    )
  );

-- Audio Files - Similar pattern
CREATE POLICY "Authenticated users can view audio files" ON audio_files
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Editors and admins can insert audio files" ON audio_files
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Editors and admins can update audio files" ON audio_files
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );

CREATE POLICY "Admins can delete audio files" ON audio_files
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role = 'admin'
    )
  );

-- ==================================================
-- ROW LEVEL SECURITY POLICIES - AUDIT LOG
-- ==================================================

-- Audit log policies
CREATE POLICY "Users can view their own audit log" ON user_audit_log
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Admins can view all audit logs" ON user_audit_log
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role = 'admin'
    )
  );

CREATE POLICY "Service role can manage audit log" ON user_audit_log
  FOR ALL USING (auth.role() = 'service_role');

-- ==================================================
-- SERVICE ROLE POLICIES (for backend operations)
-- ==================================================

CREATE POLICY "Service role has full access to user_profiles" ON user_profiles
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to news_sessions" ON news_sessions
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to articles" ON articles
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to processed_articles" ON processed_articles
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to audio_files" ON audio_files
  FOR ALL USING (auth.role() = 'service_role');

-- ==================================================
-- FUNCTIONS AND TRIGGERS
-- ==================================================

-- Function to automatically create user profile when user signs up
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO user_profiles (user_id, email, full_name, role)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'role', 'user')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile when user signs up
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Function to update user profile timestamp
CREATE OR REPLACE FUNCTION update_user_profile_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamp
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_user_profile_updated_at();

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

-- ==================================================
-- UTILITY FUNCTIONS
-- ==================================================

-- Function to get user role
CREATE OR REPLACE FUNCTION get_user_role(user_uuid UUID)
RETURNS TEXT AS $$
DECLARE
  user_role TEXT;
BEGIN
  SELECT role INTO user_role
  FROM user_profiles
  WHERE user_id = user_uuid;
  
  RETURN COALESCE(user_role, 'user');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has specific role
CREATE OR REPLACE FUNCTION user_has_role(required_role TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM user_profiles 
    WHERE user_id = auth.uid() 
    AND (
      role = required_role 
      OR (required_role = 'editor' AND role = 'admin')
      OR (required_role = 'user' AND role IN ('user', 'editor', 'admin'))
    )
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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

-- Function to log user actions
CREATE OR REPLACE FUNCTION log_user_action(
  p_action VARCHAR(100),
  p_table_name VARCHAR(100) DEFAULT NULL,
  p_record_id UUID DEFAULT NULL,
  p_details JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
  log_id UUID;
BEGIN
  INSERT INTO user_audit_log (user_id, action, table_name, record_id, details)
  VALUES (auth.uid(), p_action, p_table_name, p_record_id, p_details)
  RETURNING id INTO log_id;
  
  RETURN log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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

-- ==================================================
-- VIEWS
-- ==================================================

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

-- Create a secure view for user management (admin only)
CREATE VIEW admin_user_overview AS
SELECT 
  up.id,
  up.user_id,
  up.email,
  up.full_name,
  up.role,
  up.created_at,
  up.updated_at,
  au.email_confirmed_at,
  au.last_sign_in_at,
  (
    SELECT COUNT(*) 
    FROM user_audit_log ual 
    WHERE ual.user_id = up.user_id 
    AND ual.created_at > NOW() - INTERVAL '30 days'
  ) as activity_count_30d
FROM user_profiles up
JOIN auth.users au ON au.id = up.user_id
ORDER BY up.created_at DESC;