# Branch protection guidance

To prevent code from being merged or pushed into `main`/`master` when tests fail, enable branch protection in the repository settings and require the `Tests` workflow to pass.

Steps:

1. Go to your repository on GitHub → Settings → Branches → Branch protection rules → Add rule.
2. For `Branch name pattern` enter `main` (and create another rule for `master` if used).
3. Check `Require status checks to pass before merging`.
4. In the list of status checks, select `Tests` (the workflow we added: `.github/workflows/tests.yml`).
5. Optionally check `Include administrators` and `Require branches to be up to date before merging`.

Notes:
- A workflow cannot itself enforce protection; branch protection is a repository setting that references the workflow's status checks.
- Once enabled, pushes/PR merges that do not pass the `Tests` workflow will be blocked by GitHub.
