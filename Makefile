LOG_LEVEL ?= DEBUG

USERNAME := $(shell whoami)
TIMESTAMP := $(shell date +%Y%m%d%H%M%S)
BRANCH_NAME := $(USERNAME)-$(TIMESTAMP)

.PHONY: confirm_branch

.PHONY: clean branch push

clean:
	@git clean -fdx

branch:
	@$(MAKE) confirm_branch

confirm_branch:
	@current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$current_branch" != "main" ]; then \
		echo "You are currently on the $$current_branch branch, which is not 'main'. Do you want to create a new branch? [y/N]"; \
		read ans; \
		case $$ans in \
			[Yy]*) \
				git checkout -b $(BRANCH_NAME) ;; \
			*) \
				echo "Branch creation cancelled." ;; \
		esac; \
	else \
		git checkout -b $(BRANCH_NAME); \
	fi

push:
	@GITHUB_REPOSITORY=$$(git remote get-url origin | sed -n -e 's/^.*github\.com[:\/]\([^\/]*\)\/\([^\/]*\)\(\.git\)*$$/\1\/\2/p'); \
	if [ -z "$$GITHUB_REPOSITORY" ]; then \
		echo "Unable to determine GITHUB_REPOSITORY from the git remote origin. Please ensure you have a remote named 'origin' pointing to a GitHub repository."; \
		exit 1; \
	else \
		export GITHUB_REPOSITORY; \
	fi
	@# Check for unstaged changes and stash them if any
	@if git diff --quiet; then \
		echo "No unstaged changes detected."; \
	else \
		echo "Stashing unstaged changes."; \
		git stash push -u -m "Auto-stashed by Makefile for 'make push' command"; \
		stash_applied=1; \
	fi
	@# Update the changelog to remove 'aider: - ' prefix
	@sed -i '' -e 's/^aider: - //' CHANGELOG.md
	@# Remove 'aider:' prefix from all commit messages
	@GIT_SEQUENCE_EDITOR="sed -i '' -e 's/^pick \(.*\) aider:/pick \1 /'" git rebase -i --root --autosquash
	@if [ "$$stash_applied" = "1" ]; then \
		echo "Re-applying stashed changes."; \
		git stash pop; \
	fi
	@# Update the changelog to remove 'aider: - ' prefix
	@sed -i '' -e 's/aider: - //g' CHANGELOG.md
	python3 push_script.py
