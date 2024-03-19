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
		git diff --name-only main...$$current_branch | xargs -I {} git diff main...$$current_branch -- {} | curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $$OPENAI_API_KEY" --data-binary @- https://api.openai.com/v1/chat/completions --data '{"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are an expert software engineer.\nReview the provided context and diffs which are about to be committed to a git repo.\nGenerate a *SHORT* 1 line, 1 sentence commit message that describes the changes.\nThe commit message MUST be in the past tense.\nIt must describe the changes *which have been made* in the diffs!\nReply with JUST the commit message, without quotes, comments, questions, etc!"}]}' > commit_message.txt; \
		echo "Changelog generated."; \
		echo "Changelog content:"; \
		cat changelog.txt; \
		echo "Generating pull request notes..."; \
		git diff --name-only main...$$current_branch | xargs -I {} git diff main...$$current_branch -- {} | curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $$OPENAI_API_KEY" --data-binary @- https://api.openai.com/v1/chat/completions --data '{"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are an expert software engineer.\nReview the provided context and diffs which are about to be added to a git repo pull request.\nBreak the changes into logical chunks and generate a *SHORT* 1 line, 1 sentence\nmessage that concisely and accurately describes each change.\nThe message MUST be in the past tense.\nIt must describe the changes *which have been made* in the diffs!\nReply with JUST the pull request message, without quotes, comments, questions, etc!"}]}' > pr_notes.txt; \
		echo "Pull request notes generated."; \
		echo "Pull request notes content:"; \
		cat pr_notes.txt; \
		git push origin $$current_branch; \
	fi
