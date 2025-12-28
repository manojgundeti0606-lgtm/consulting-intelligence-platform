# Consulting Intelligence Platform - Google Cloud Deployment Guide

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed ([Download](https://cloud.google.com/sdk/docs/install))
3. **Docker** installed (for local testing)

## Files Created for Deployment

| File | Purpose |
|------|---------|
| `Dockerfile` | Container image definition |
| `.dockerignore` | Files to exclude from image |
| `requirements.txt` | Python dependencies |

---

## Option 1: Google Cloud Run (Recommended)

Cloud Run is serverless, auto-scales, and you only pay for what you use.

### Step 1: Set Up Project

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Step 2: Set Environment Variables as Secrets

```bash
# Create secrets for sensitive data
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "your-smtp-password" | gcloud secrets create SMTP_PASSWORD --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 3: Build and Deploy

```bash
# Navigate to your app directory
cd path/to/gem_scraper

# Build and deploy in one command
gcloud run deploy cip-app \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars "GEMINI_API_KEY=your-key-here" \
    --set-env-vars "SMTP_SERVER=smtp.gmail.com" \
    --set-env-vars "SMTP_PORT=587" \
    --set-env-vars "SENDER_EMAIL=your-email@gmail.com" \
    --set-env-vars "SENDER_PASSWORD=your-app-password" \
    --set-env-vars "EMAIL_ENABLED=true"
```

### Step 4: Get Your App URL

After deployment, you'll get a URL like:

```
https://cip-app-xxxxx-uc.a.run.app
```

---

## Option 2: Google App Engine

App Engine is simpler but less flexible.

### Create app.yaml

```yaml
runtime: python311

instance_class: F2

entrypoint: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true

env_variables:
  GEMINI_API_KEY: "your-api-key"
  SMTP_SERVER: "smtp.gmail.com"
  SMTP_PORT: "587"
  SENDER_EMAIL: "your-email@gmail.com"
  SENDER_PASSWORD: "your-app-password"
  EMAIL_ENABLED: "true"
```

### Deploy

```bash
gcloud app deploy
```

---

## Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
| `SMTP_SERVER` | Email SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SENDER_EMAIL` | Email sender address | `you@gmail.com` |
| `SENDER_PASSWORD` | Gmail App Password | `xxxx xxxx xxxx` |
| `EMAIL_ENABLED` | Enable email notifications | `true` |
| `APP_URL` | Your deployed app URL | `https://your-app.run.app` |

---

## Important Notes

### 1. Database Persistence

Cloud Run containers are **ephemeral**. For persistent data:

- Use **Cloud SQL** (PostgreSQL/MySQL)
- Or **Firestore** (NoSQL)
- Or mount a **Cloud Storage** bucket

### 2. Google OAuth

Update your OAuth redirect URIs in Google Cloud Console:

```
https://your-app-xxxxx.run.app
https://your-app-xxxxx.run.app/oauth2callback
```

### 3. Secrets Management

Never commit secrets to code! Use:

- **Secret Manager** for production
- Environment variables set via `--set-env-vars`

### 4. Costs

- Cloud Run: ~$0 for low traffic (free tier: 2M requests/month)
- App Engine: ~$0 for F1 instance with low traffic

---

## Quick Deploy Commands

```bash
# 1. Login
gcloud auth login

# 2. Set project
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy (from app directory)
gcloud run deploy cip-app --source . --region us-central1 --allow-unauthenticated
```

After deployment, update `APP_URL` in your environment to match the Cloud Run URL for email deep links to work!
