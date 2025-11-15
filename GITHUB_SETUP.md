# Setting up GitHub Repository "tech-haiku2"

## Step 1: Create the Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `tech-haiku2`
3. Choose Public or Private
4. **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

## Step 2: Push Your Code

After creating the repository, GitHub will show you commands. Use these:

```bash
cd /Users/ruthannlarsen/another_haiku

# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tech-haiku2.git

# Push to GitHub
git push -u origin main
```

Or if you prefer SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/tech-haiku2.git
git push -u origin main
```

## Step 3: Deploy on Vercel

Once the code is on GitHub:

1. Go to https://vercel.com
2. Click "Add New Project"
3. Import the `tech-haiku2` repository
4. Vercel will auto-detect Flask
5. Click "Deploy"

That's it! Your app will be live on Vercel.

