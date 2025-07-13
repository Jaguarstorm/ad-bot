# AdForgeAI - AI-Powered Video Creation & Social Media Automation

## 🚀 Overview
AdForgeAI is a comprehensive AI-powered video creation and social media automation platform. Upload videos, let AI edit them for different platforms, or generate complete videos from topics - then automatically post to all your social media accounts.

## ✨ Features

### 🎬 Smart Video Editor
- **Auto Scene Detection**: AI identifies the most engaging moments
- **Platform Optimization**: Auto-crops for TikTok (9:16), YouTube Shorts, Instagram Reels
- **AI Subtitles**: Automatic speech-to-text with stylish captions
- **Smart Thumbnails**: AI picks the best frame for thumbnails

### 🤖 AI Video Generator
- **Topic to Video**: Type a topic, get a complete video with voiceover
- **AI Script Writing**: GPT-powered engaging scripts
- **Voice Synthesis**: ElevenLabs AI voice generation
- **Stock Footage**: Automatic relevant clip selection

### 📱 Multi-Platform Posting
- **One-Click Post**: Upload once, post to TikTok, YouTube, Instagram, Facebook, Twitter
- **Auto Scheduling**: Set posting times or let AI optimize
- **Platform-Specific Captions**: AI generates optimized content per platform

### 💳 Subscription Plans
- **15-Day Free Trial**: Full access to test all features
- **Basic Plan ($15/month)**: Smart Editor, AI captions, manual scheduling
- **Pro Plan ($40/month)**: AI Video Generator, auto-posting, unlimited usage

## 🏗️ Architecture

```
AdForgeAI/
├── frontend/           # React web app + Electron desktop
├── backend/            # FastAPI server
├── ai_engine/          # AI video processing
├── mobile/             # Flutter mobile app
├── billing/            # Stripe + Google Play billing
└── docs/              # Documentation
```

## 🛠️ Tech Stack
- **Frontend**: React.js + TailwindCSS + Electron
- **Backend**: Python FastAPI
- **AI**: OpenAI GPT-4, Whisper, ElevenLabs
- **Video**: MoviePy, OpenCV, FFmpeg
- **Database**: PostgreSQL (Supabase)
- **Billing**: Stripe + Google Play Billing
- **Hosting**: Vercel (frontend) + Render (backend)

## 📊 Revenue Projections
- **100 Basic Users**: ~$1,275/month profit
- **1000 Basic Users**: ~$12,915/month profit
- **Breakeven**: ~10 users

## 🔐 Security & Privacy
- **User Isolation**: Each user's data is completely isolated
- **Encrypted Tokens**: OAuth tokens encrypted with AES
- **No Admin Access**: Even developers cannot access user content
- **GDPR Compliant**: Full data deletion rights

## 🚀 Quick Start
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run backend: `python backend/main.py`
5. Run frontend: `npm start`

## 📄 Legal
- **Terms & Conditions**: Users must agree before accessing app
- **Privacy Policy**: Full data protection compliance
- **Liability**: Users use at own risk, no warranties provided

## 🎯 Target Platforms
- **Web**: Browser-based application
- **Windows**: Desktop app (.exe installer)
- **Android**: Google Play Store app
- **iOS**: Future release

---

**Built by Jaguar Storm** - AI That Haunts the Algorithm 