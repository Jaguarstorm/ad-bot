# AdForgeAI Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL database (Supabase recommended)
- FFmpeg installed on server
- Domain name (optional)

## 📋 Step-by-Step Deployment

### 1. Backend Deployment (FastAPI)

#### Option A: Render.com (Recommended)
1. Fork/clone this repository to your GitHub
2. Connect your GitHub repo to Render
3. Create a new Web Service
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9

#### Option B: Railway.app
1. Connect your GitHub repo to Railway
2. Create new service from GitHub repo
3. Set environment variables (see below)
4. Deploy automatically

#### Option C: DigitalOcean App Platform
1. Connect your GitHub repo
2. Select Python as runtime
3. Set build and run commands
4. Configure environment variables

### 2. Frontend Deployment (React)

#### Option A: Vercel (Recommended)
1. Connect your GitHub repo to Vercel
2. Set build settings:
   - **Framework Preset**: Create React App
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/build`
3. Set environment variables for API URL

#### Option B: Netlify
1. Connect your GitHub repo to Netlify
2. Set build command: `cd frontend && npm run build`
3. Set publish directory: `frontend/build`

### 3. Database Setup (Supabase)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Get your project URL and anon key
4. Run the SQL commands below in the SQL editor

```sql
-- Create user_profiles table
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  plan TEXT DEFAULT 'trial',
  trial_start TIMESTAMP DEFAULT now(),
  stripe_customer_id TEXT,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Create user_tokens table
CREATE TABLE user_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  UNIQUE(user_id, platform)
);

-- Create videos table
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  original_path TEXT NOT NULL,
  processed_path TEXT,
  thumbnail_path TEXT,
  title TEXT,
  description TEXT,
  duration INTEGER,
  file_size INTEGER,
  status TEXT DEFAULT 'uploaded',
  created_at TIMESTAMP DEFAULT now()
);

-- Create scheduled_posts table
CREATE TABLE scheduled_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  video_id UUID REFERENCES videos(id),
  platforms TEXT[] NOT NULL,
  caption TEXT,
  scheduled_at TIMESTAMP NOT NULL,
  status TEXT DEFAULT 'pending',
  posted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT now()
);

-- Create user_agreements table
CREATE TABLE user_agreements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  agreed_at TIMESTAMP DEFAULT now(),
  app_version TEXT DEFAULT '1.0.0'
);

-- Create subscriptions table
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_subscription_id TEXT UNIQUE NOT NULL,
  plan TEXT NOT NULL,
  status TEXT NOT NULL,
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Create analytics table
CREATE TABLE analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  uploads INTEGER DEFAULT 0,
  ai_captions INTEGER DEFAULT 0,
  subtitles INTEGER DEFAULT 0,
  generated_videos INTEGER DEFAULT 0,
  posts_scheduled INTEGER DEFAULT 0,
  posts_published INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE(user_id, date)
);

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES ('user-videos', 'user-videos', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('thumbnails', 'thumbnails', true);
INSERT INTO storage.buckets (id, name, public) VALUES ('voiceovers', 'voiceovers', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('generated', 'generated', false);

-- Set up RLS policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;

-- User can only access their own data
CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can view own tokens" ON user_tokens FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own tokens" ON user_tokens FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own tokens" ON user_tokens FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own tokens" ON user_tokens FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own videos" ON videos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own videos" ON videos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own videos" ON videos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own videos" ON videos FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own posts" ON scheduled_posts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own posts" ON scheduled_posts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own posts" ON scheduled_posts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own posts" ON scheduled_posts FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own agreements" ON user_agreements FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own agreements" ON user_agreements FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own subscriptions" ON subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own subscriptions" ON subscriptions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own subscriptions" ON subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own analytics" ON analytics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own analytics" ON analytics FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own analytics" ON analytics FOR INSERT WITH CHECK (auth.uid() = user_id);
```

### 4. Environment Variables

Set these environment variables in your deployment platform:

```bash
# Copy from env_template.txt and fill in your values
DEBUG=False
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
OPENAI_API_KEY=sk-your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
JWT_SECRET_KEY=your-32-character-jwt-secret
TOKEN_AES_SECRET=your-32-character-aes-secret
```

### 5. API Keys Setup

#### OpenAI
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account and get API key
3. Add billing information

#### ElevenLabs
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Create account and get API key
3. Choose a plan (free tier available)

#### Stripe
1. Go to [stripe.com](https://stripe.com)
2. Create account and get API keys
3. Set up webhook endpoint: `https://your-backend.com/api/billing/webhook`
4. Create products and prices for Basic ($15) and Pro ($40) plans

#### Social Media APIs
- **YouTube**: Google Cloud Console → YouTube Data API v3
- **Instagram**: Meta for Developers → Instagram Basic Display API
- **TikTok**: TikTok for Developers → OpenAPI
- **Twitter**: Twitter Developer Portal → API v2

### 6. Domain & SSL Setup

1. Point your domain to your hosting provider
2. Enable SSL/HTTPS (automatic on most platforms)
3. Update CORS settings in backend/config.py
4. Update frontend API URL

### 7. Testing Deployment

1. Test user registration/login
2. Test video upload
3. Test AI features
4. Test billing integration
5. Test social media connections

## 🔧 Local Development Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Database
- Use Supabase local development or cloud instance
- Set up environment variables in .env file

## 📱 Mobile App Deployment

### Android (Google Play Store)
1. Set up Flutter development environment
2. Build APK: `flutter build apk --release`
3. Create Google Play Console account
4. Upload APK and set up in-app billing
5. Configure OAuth for social media platforms

### iOS (App Store)
1. Set up iOS development environment
2. Build IPA: `flutter build ios --release`
3. Create Apple Developer account
4. Upload to App Store Connect
5. Configure in-app purchases

## 🔒 Security Checklist

- [ ] All API keys are environment variables
- [ ] JWT secret is 32+ characters
- [ ] AES encryption key is secure
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] Input validation is implemented
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] HTTPS is enabled
- [ ] Database backups are configured

## 📊 Monitoring & Analytics

### Recommended Tools
- **Backend**: Sentry for error tracking
- **Frontend**: Google Analytics
- **Database**: Supabase dashboard
- **Performance**: Vercel Analytics

### Health Checks
- Set up `/health` endpoint
- Monitor API response times
- Track error rates
- Monitor database performance

## 🚀 Production Optimization

### Backend
- Enable Redis for caching
- Set up CDN for static files
- Configure auto-scaling
- Set up monitoring alerts

### Frontend
- Enable code splitting
- Optimize bundle size
- Set up PWA features
- Configure service workers

### Database
- Set up read replicas
- Optimize queries
- Configure connection pooling
- Set up automated backups

## 📞 Support

For deployment issues:
1. Check logs in your hosting platform
2. Verify environment variables
3. Test API endpoints
4. Check database connections
5. Review CORS settings

---

**Built by Jaguar Storm** - AI That Haunts the Algorithm 