# Publish this prepared repository

Suggested name: `semiconductor-data-discovery`.

If you received this as a ZIP, extract it and open a terminal in the extracted project directory. To initialize source control:

```bash
git init -b main
git add .
git commit -m "Build semiconductor metadata discovery demo"
```

With the official GitHub CLI already installed and authenticated:

```bash
gh repo create semiconductor-data-discovery --private --source=. --remote=origin --push
```

This creates a private repository by default for review. Change visibility only when you decide to share it more widely. This command was not executed during preparation because remote repository creation was blocked by browser sign-in.

Alternatively, create a repository through GitHub's normal new-repository page, then use the exact remote URL GitHub supplies:

```bash
git remote add origin YOUR_REPOSITORY_REMOTE_URL
git push -u origin main
```

Do not initialize that remote with a README if you plan to push this prepared history. Keep `.env` files and credentials out of commits.
