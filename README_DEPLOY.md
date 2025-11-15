# Deploying to Vercel

## Prerequisites
1. Install Vercel CLI: `npm i -g vercel`
2. Have a Vercel account (sign up at vercel.com)

## Deployment Steps

1. **Login to Vercel:**
   ```bash
   vercel login
   ```

2. **Deploy the application:**
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Link to existing project or create new
   - Confirm project settings
   - Deploy

3. **For production deployment:**
   ```bash
   vercel --prod
   ```

## Important Notes

- The app uses global state (word_pool, used_words) which will reset on each serverless function invocation
- Consider using Vercel KV or a database for persistent storage if needed
- The initial scrape will run on first request, which may cause a slight delay
- All routes are handled by the Flask app through the vercel.json configuration

## Environment Variables (if needed)

If you need to set environment variables:
```bash
vercel env add VARIABLE_NAME
```

Or set them in the Vercel dashboard under Project Settings > Environment Variables.

