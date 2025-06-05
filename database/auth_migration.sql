-- Authentication Migration for TKR News Gatherer
-- Adds user authentication and proper RLS policies

-- Create user profiles table to extend Supabase auth.users
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  email VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'editor', 'admin')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);

-- Enable RLS on user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

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

-- Update existing RLS policies to require authentication

-- Drop existing public policies
DROP POLICY IF EXISTS "Public can view news sessions" ON news_sessions;
DROP POLICY IF EXISTS "Public can view articles" ON articles;
DROP POLICY IF EXISTS "Public can view processed articles" ON processed_articles;
DROP POLICY IF EXISTS "Public can view audio files" ON audio_files;

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

-- Service role maintains full access
CREATE POLICY "Service role has full access to user_profiles" ON user_profiles
  FOR ALL USING (auth.role() = 'service_role');

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

-- Add audit logging for user actions
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