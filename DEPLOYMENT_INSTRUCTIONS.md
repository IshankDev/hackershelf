# Deployment Instructions

## GitHub Pages Setup (Required)

The site is ready to deploy, but GitHub Pages must be enabled in the repository settings.

### Step 1: Enable GitHub Pages

1. Go to repository settings: https://github.com/IshankDev/hackershelf/settings/pages
2. Under "Build and deployment":
   - **Source:** Select "GitHub Actions" from the dropdown
3. Click "Save"

### Step 2: Trigger Deployment

After enabling Pages, the site will deploy automatically on the next push. You can:

**Option A:** Re-run the failed workflow
```bash
gh workflow run deploy.yml
```

**Option B:** Make any small change and push
```bash
git commit --allow-empty -m "Trigger Pages deployment"
git push
```

**Option C:** Manually trigger via GitHub UI
- Go to: https://github.com/IshankDev/hackershelf/actions
- Click "Deploy to GitHub Pages"
- Click "Run workflow"

### Step 3: Verify Deployment

Monitor the deployment:
```bash
gh run list --workflow=deploy.yml --limit 1
```

Or visit: https://github.com/IshankDev/hackershelf/actions

Once successful, the site will be live at:
**https://ishankdev.github.io/hackershelf/**

### Troubleshooting

**If deployment still fails:**

1. Check workflow logs:
```bash
gh run view --log
```

2. Verify Pages source is set to "GitHub Actions" (not "Deploy from a branch")

3. Ensure the repository is public (Pages may be disabled for private repos on free accounts)

4. Check that the workflow file exists:
```bash
cat .github/workflows/deploy.yml
```

## Local Testing

To test the site locally before deploying:

```bash
cd site
python3 -m http.server 8000
```

Then visit: http://localhost:8000

## Deployment Architecture

```
Push to main
    ↓
GitHub Actions Workflow (.github/workflows/deploy.yml)
    ↓
1. Checkout code
2. Configure Pages
3. Upload site/ folder as artifact
4. Deploy artifact to GitHub Pages
    ↓
Live at https://ishankdev.github.io/hackershelf/
```

## What Gets Deployed

Only the `site/` directory is deployed:
- `index.html` — Main page
- `css/style.css` — All styles
- `js/app.js` — Client-side app
- `data/` — JSON data files (books, mentions, stats)
- `download/` — Data package ZIP

The `pipeline/` directory and raw data files are NOT deployed (they're for regenerating data).

## Updating the Site

### Update Content

To update book data:

1. Run the pipeline (see PIPELINE_README.md)
2. Commit updated files in `site/data/`
3. Push to main
4. Deployment happens automatically

### Update Code

To update the UI or functionality:

1. Edit files in `site/` (HTML, CSS, or JS)
2. Test locally: `cd site && python3 -m http.server 8000`
3. Commit changes
4. Push to main
5. Deployment happens automatically

## Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file to `site/` with your domain:
```bash
echo "hackershelf.yourdomain.com" > site/CNAME
```

2. Configure DNS:
   - Add CNAME record: `hackershelf.yourdomain.com` → `ishankdev.github.io`

3. In GitHub repo settings → Pages:
   - Add custom domain
   - Enforce HTTPS

## Deployment Timeline

From commit to live: ~1-2 minutes

- Workflow trigger: instant
- Build: ~10-20 seconds
- Deploy: ~30-60 seconds
- DNS propagation: instant (for github.io subdomain)

## Security Notes

- All data is static JSON (no server-side code)
- No API keys or secrets needed for deployment
- User data (want-to-read list, theme) stored in browser localStorage only
- Safe to deploy publicly

## Monitoring

Check deployment status anytime:

```bash
# Latest run
gh run list --workflow=deploy.yml --limit 1

# Watch a specific run
gh run watch 41467926181

# View logs
gh run view --log
```

Or visit the Actions tab: https://github.com/IshankDev/hackershelf/actions

## Rollback

To rollback to a previous version:

1. Find the commit SHA of the working version
2. Reset to that commit:
```bash
git reset --hard <commit-sha>
git push --force
```

Or revert specific commits:
```bash
git revert <commit-sha>
git push
```

## Next Steps

After Pages is enabled and the site is live:

1. ✅ Verify the site loads: https://ishankdev.github.io/hackershelf/
2. ✅ Test all pages (home, browse, book detail, list, about)
3. ✅ Test search and filters
4. ✅ Test dark mode toggle
5. ✅ Test want-to-read list (localStorage)
6. 📝 Update the README with the live URL if you change it
7. 🚀 Share with the HN community!

## Support

If deployment issues persist, check:
- GitHub Status: https://www.githubstatus.com/
- GitHub Pages docs: https://docs.github.com/en/pages
- Actions docs: https://docs.github.com/en/actions
