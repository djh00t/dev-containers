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
	@current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$current_branch" = "main" ]; then \
		git checkout -b $(BRANCH_NAME); \
		git tag -a $(BRANCH_NAME) -m "Release $(BRANCH_NAME)"; \
		git push origin $(BRANCH_NAME) --tags; \
	else \
		echo "Generating changelog from diffs..."; \
		git diff --name-only main...$$current_branch | xargs -I {} git diff main...$$current_branch -- {} | curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $$OPENAI_API_KEY" --data-binary @- https://api.openai.com/v1/chat/completions -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are an expert software engineer. Review the provided diffs and break them into logical changes. For the commit message you will generate a *SHORT* 1 line, 1 sentence overall commit summary that gives a high level explanation of the changes. For the PR notes you will generate a *SHORT* 1 line, 1 sentence message per change that describes the intended outcome of each change, return the list of changes in a bullet point list. Each returned message MUST be in the past tense. It must describe the changes *which have been made* in the diffs! Reply with JUST the commit message and the PR notes, without quotes, comments, questions, etc!"}]}' > changelog.txt; \
		echo "Changelog generated."; \
		echo "Changelog content:"; \
		cat changelog.txt; \
		git push origin $$current_branch; \
	fi
