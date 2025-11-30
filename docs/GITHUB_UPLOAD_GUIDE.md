# 📤 GitHub Upload Guide - TS_OPAC eLibrary

**Date:** November 30, 2025  
**Repository:** TS_OPAC eLibrary (v1.0-pre)  
**Size:** ~486 MB repository + 32.95 MB database

---

## 🎯 QUICK START (5 minutes)

### **If you don't have a GitHub account yet:**
1. Go to https://github.com
2. Click "Sign up"
3. Create account with your email
4. Verify email

### **If you already have GitHub:**
Skip to **STEP 1: Create Repository on GitHub** below

---

## 📍 DETAILED INSTRUCTIONS

### **STEP 1: Create a New Repository on GitHub**

1. **Login to GitHub:** https://github.com (login if not already)

2. **Create New Repository:**
   - Click **+** icon (top right) → **New repository**
   - OR go to https://github.com/new

3. **Fill Repository Details:**
   ```
   Repository name: TS_OPAC_eLibrary
   Description: A modern web-based library management system
                built with Django. Features publication catalog,
                inventory management, circulation system, and
                role-based access control.
   
   Visibility: Public (or Private if you prefer)
   
   Initialize with:
   ☐ Add a README file (NO - we have our own)
   ☐ Add .gitignore (NO - we have our own)
   ☐ Choose a license (OPTIONAL - MIT recommended)
   ```

4. **Click "Create repository"**

5. **You'll see instructions** - Skip these, we'll use the command line below

---

### **STEP 2: Add GitHub Remote to Your Local Repository**

Open PowerShell in your project directory and run:

```powershell
cd c:\Users\Dang\Desktop\TS_OPAC_eLibrary
```

Add the GitHub remote:
```bash
git remote add origin https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

Example:
```bash
git remote add origin https://github.com/dang/TS_OPAC_eLibrary.git
```

Verify it worked:
```bash
git remote -v
```

Expected output:
```
origin  https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git (fetch)
origin  https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git (push)
```

---

### **STEP 3: Push Your Repository to GitHub**

Push all commits:
```bash
git branch -M main
git push -u origin main
```

This will:
- Rename `master` branch to `main` (GitHub standard)
- Push all commits to GitHub
- Set upstream tracking

**If prompted for login:**
- Use your GitHub username
- For password, use a **Personal Access Token** (not your password)
  - Generate at: https://github.com/settings/tokens/new
  - Scope needed: `repo` (Full control of private repositories)
  - Copy token and paste when prompted

Push your tags:
```bash
git push origin --tags
```

This pushes the `v1.0-pre` backup tag to GitHub.

---

### **STEP 4: Verify Upload**

1. **Visit your GitHub repository:**
   ```
   https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary
   ```

2. **Check you see:**
   - ✅ All files in root directory
   - ✅ `docs/` folder with documentation
   - ✅ `accounts/`, `catalog/`, `circulation/` apps
   - ✅ `templates/`, `static/` folders
   - ✅ `manage.py`, `requirements.txt`, etc.
   - ✅ Commit history (63 commits)
   - ✅ `v1.0-pre` tag in releases

3. **If everything looks good:**
   Congratulations! Your repository is now on GitHub! 🎉

---

## 💾 COMMAND QUICK REFERENCE

**Add remote:**
```bash
git remote add origin https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git
```

**Push all branches:**
```bash
git branch -M main
git push -u origin main
```

**Push all tags:**
```bash
git push origin --tags
```

**Check remote:**
```bash
git remote -v
```

**Change remote URL (if you made a mistake):**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git
```

---

## 🔐 AUTHENTICATION OPTIONS

### **Option 1: Personal Access Token (RECOMMENDED)**

1. Go to https://github.com/settings/tokens/new
2. Name it: `TS_OPAC_Upload`
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
4. Click "Generate token"
5. Copy the token (you won't see it again!)
6. When `git push` asks for password, paste the token

**Advantages:**
- More secure than password
- Can be revoked anytime
- Limited scope access

### **Option 2: SSH Key (ADVANCED)**

1. Generate SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. Add to GitHub: https://github.com/settings/keys

3. Use SSH URL:
   ```bash
   git remote add origin git@github.com:YOUR_USERNAME/TS_OPAC_eLibrary.git
   ```

4. Push:
   ```bash
   git push -u origin main
   ```

---

## 📋 FULL CHECKLIST

### Before Upload:
- [ ] Created GitHub account
- [ ] Created new repository on GitHub
- [ ] Have GitHub username ready
- [ ] Have Personal Access Token ready (or SSH key)

### During Upload:
- [ ] Added GitHub remote: `git remote add origin ...`
- [ ] Verified remote: `git remote -v`
- [ ] Renamed branch: `git branch -M main`
- [ ] Pushed commits: `git push -u origin main`
- [ ] Pushed tags: `git push origin --tags`

### After Upload:
- [ ] Verified repository visible on GitHub
- [ ] All files present
- [ ] Commit history visible
- [ ] Tags visible
- [ ] README shows correctly

---

## 🎯 WHAT GETS UPLOADED

**Will Upload (1,000+ files, 62 commits):**
- ✅ All source code (Django apps)
- ✅ All documentation (30+ markdown files)
- ✅ All templates (HTML)
- ✅ All static files (CSS, JS)
- ✅ requirements.txt (dependencies)
- ✅ Configuration files (.env.example, etc.)
- ✅ All git history (62 commits)
- ✅ Git tags (v1.0-pre)

**Will NOT Upload (files in .gitignore):**
- ❌ `db.sqlite3` (database file)
- ❌ `venv/` (virtual environment)
- ❌ `__pycache__/` (Python cache)
- ❌ `.env` (sensitive environment variables)
- ❌ `.DS_Store` (Mac files)
- ❌ `*.pyc` (compiled Python)

---

## ⚠️ IMPORTANT NOTES

### Database & Secrets
- Your database (`db.sqlite3`) is NOT in git - it's in `.gitignore`
- This is **good for security** - real data not exposed
- Users can generate fresh data with `python setup_demo_data.py`

### Environment Variables
- `.env` file is NOT in git (in `.gitignore`)
- `.env.example` shows template (safe to upload)
- Users copy `.env.example` → `.env` and fill in values

### Size Consideration
- Repository is small (~500 MB)
- No large files or binaries
- Uploads quickly even on slow internet

### Public vs Private
- **Public:** Anyone can see/download but can't modify
- **Private:** Only invited users can see
- Can change anytime in GitHub Settings

---

## 🚀 AFTER UPLOAD

### **Share Your Repository**

1. **Get the URL:**
   ```
   https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary
   ```

2. **Add to README (Optional):**
   Create/edit your GitHub profile README to mention this project

3. **Add a License (Optional):**
   - Click "Add file" → "Create new file"
   - Name: `LICENSE`
   - Choose license (MIT recommended for open source)
   - Commit

4. **Add Topics (Optional):**
   - Go to repository Settings
   - Add topics: `django`, `library-management`, `python`

### **Others Can Now:**
- Clone: `git clone https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git`
- View code online
- Download as ZIP
- Fork and contribute (if public)

---

## ❓ TROUBLESHOOTING

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/TS_OPAC_eLibrary.git
```

### "Authentication failed"
1. Verify username is correct
2. Use Personal Access Token (not password)
3. Token has `repo` scope selected
4. Token hasn't expired

### "Permission denied (publickey)"
- You're using SSH but haven't set up SSH key
- Use HTTPS URL instead
- OR follow SSH Key setup in this guide

### Files missing after upload
- Check `.gitignore` - files in it won't upload
- Check files are committed: `git status`
- Try: `git push -u origin main` again

### Want to update after uploading
1. Make changes locally
2. Commit: `git commit -m "message"`
3. Push: `git push origin main`

---

## 📚 HELPFUL LINKS

- **GitHub Docs:** https://docs.github.com
- **Git Guide:** https://git-scm.com/doc
- **Personal Access Token:** https://github.com/settings/tokens
- **SSH Keys:** https://github.com/settings/keys

---

## ✨ SUMMARY

| Step | Action | Time |
|------|--------|------|
| 1 | Create GitHub account (if needed) | 2 min |
| 2 | Create repository on GitHub | 1 min |
| 3 | Add remote to local repo | 1 min |
| 4 | Push commits to GitHub | 2 min |
| 5 | Push tags to GitHub | 1 min |
| 6 | Verify on GitHub website | 1 min |
| **Total** | | **8 minutes** |

---

## 🎉 YOU'RE DONE!

Once complete:
- Your code is backed up on GitHub
- Others can access your repository
- You can collaborate easily
- Version history is preserved
- Your project is discoverable

**Next steps:**
1. Share the GitHub link with stakeholders
2. Continue development if needed
3. Deploy to production when ready
4. Keep pushing updates to GitHub

---

**Happy coding! 🚀**
