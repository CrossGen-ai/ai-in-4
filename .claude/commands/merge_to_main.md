# Merge Branch to Main with Database Rebuild

Merge the current branch into main and rebuild the database to match the merged schema.

## Variables

None required - operates on current branch.

## Instructions

- Merge the current branch into main
- After merge, rebuild the database to ensure schema matches the merged models
- Ensure no conflicts exist before merging
- If conflicts exist, report them and stop

## Run

**Check Current Status:**
- Run `git branch --show-current` to get the current branch name
- Run `git status` to check for uncommitted changes

**Merge to Main:**
- Run `git checkout main` to switch to main branch
- Run `git pull origin main` to get latest changes
- Run `git merge <current_branch_name> --no-ff` to merge with merge commit
- If merge conflicts occur, stop and report them

**Rebuild Database:**
- Run `rm -f app/server/db/database.db` to remove old database
- Run `cd app/server && python3 -m db.init_db` to create fresh schema
- Run `cd app/server && python3 -m db.seed_db` to populate seed data

**Push Changes:**
- Run `git push origin main` to push merged changes

## Report

After completing the merge and database rebuild:
- Report the branch that was merged
- Report success message: "Merged <branch_name> to main and rebuilt database"
- List any issues encountered
