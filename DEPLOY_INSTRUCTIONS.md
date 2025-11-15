# Step-by-Step Vercel Deployment Instructions

## Option 1: Deploy via Vercel Dashboard (Easiest)

1. **Go to [vercel.com](https://vercel.com)** and sign up/login
2. **Click "Add New Project"**
3. **Import your Git repository** (GitHub, GitLab, or Bitbucket)
   - If you haven't pushed to Git yet, do that first:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git remote add origin <your-repo-url>
     git push -u origin main
     ```
4. **Vercel will auto-detect** the Flask app
5. **Click Deploy**

## Option 2: Deploy via CLI

### Step 1: Login to Vercel
```bash
cd /Users/ruthannlarsen/another_haiku
npx vercel login
```
- This will open a browser window
- Complete the authentication
- Return to terminal when done

### Step 2: Deploy
```bash
npx vercel
```
- Follow the prompts:
  - **Set up and deploy?** → Yes
  - **Which scope?** → Select your account
  - **Link to existing project?** → No (first time) or Yes (if updating)
  - **Project name?** → Press Enter for default or type a name
  - **Directory?** → Press Enter (current directory)
  - **Override settings?** → No

### Step 3: Deploy to Production
```bash
npx vercel --prod
```

## Troubleshooting

If you get errors:

1. **Check Python version**: Vercel uses Python 3.9 by default. Add `runtime.txt`:
   ```
   python-3.9
   ```

2. **Check build logs** in Vercel dashboard for specific errors

3. **Test locally first**:
   ```bash
   python3 app.py
   ```

## Files Created for Deployment:
- ✅ `vercel.json` - Vercel configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `.vercelignore` - Files to exclude

Your app should be accessible at: `https://your-project-name.vercel.app`

