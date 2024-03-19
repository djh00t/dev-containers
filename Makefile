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
	@set -e; \
	current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$current_branch" = "main" ]; then \
		git checkout -b $(BRANCH_NAME); \
		git tag -a $(BRANCH_NAME) -m "Release $(BRANCH_NAME)"; \
		git push origin $(BRANCH_NAME) --tags; \
	else \
		if [ "$$LOG_LEVEL" = "DEBUG" ]; then \
			echo "Debug logging is enabled. Displaying diffs..."; \
			git diff --name-only main...$$current_branch | xargs -I {} git diff main...$$current_branch -- {}; \
		fi; \
		diff_content=$$(git diff --name-only main...$$current_branch | xargs -I {} git diff main...$$current_branch -- {}); \
		json_payload=$$(echo "{\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"system\", \"content\": \"You are an expert software engineer. Review the provided context and diffs which are about to be committed to a git repo. Generate a *SHORT* 1 line, 1 sentence commit message that describes the changes. The commit message MUST be in the past tense. It must describe the changes *which have been made* in the diffs! Reply with JUST the commit message, without quotes, comments, questions, etc!\"}, {\"role\": \"user\", \"content\": \"$(echo "$diff_content" | jq -aRs .)\"}]}" | jq -c .); \
		if [ "$$LOG_LEVEL" = "DEBUG" ]; then \
			echo "JSON payload for OpenAI API:"; \
			echo "$$json_payload"; \
		fi; \
		echo $$json_payload | curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $$OPENAI_API_KEY" -d @- https://api.openai.com/v1/chat/completions > commit_message.txt; \
		json_payload=$$(echo "{\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"system\", \"content\": \"You are an expert software engineer. Review the provided context and diffs which are about to be committed to a git repo. Generate a *SHORT* 1 line, 1 sentence commit message that describes the changes. The commit message MUST be in the past tense. It must describe the changes *which have been made* in the diffs! Reply with JUST the commit message, without quotes, comments, questions, etc!\"}]}" | jq -c .); \
		if [ "$$LOG_LEVEL" = "DEBUG" ]; then \
			echo "JSON payload for OpenAI API:"; \
			echo "$$json_payload"; \
		fi; \
		curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $$OPENAI_API_KEY" -d "$$json_payload" https://api.openai.com/v1/chat/completions > commit_message.txt; \
		echo "Changelog generated."; \
		echo "Changelog content:"; \
		cat changelog.txt; \
		echo "Changelog generated."; \
		if [ "$$LOG_LEVEL" = "DEBUG" ]; then \
			echo "Commit message content:"; \
			cat commit_message.txt; \
		fi; \
		echo "Generating pull request notes..."; \
		json_payload_pr=$$(echo "{\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"system\", \"content\": \"You are an expert software engineer. Review the provided context and diffs which are about to be added to a git repo pull request. Break the changes into logical chunks and generate a *SHORT* 1 line, 1 sentence message that concisely and accurately describes each change. The message MUST be in the past tense. It must describe the changes *which have been made* in the diffs! Reply with JUST the pull request message, without quotes, comments, questions, etc!\"}]}" | jq -c .); \
		git diff --name-only main...$$current_branch | xargs -I {} git diff main...$$current_branch -- {} | curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $$OPENAI_API_KEY" -d "$$json_payload_pr" https://api.openai.com/v1/chat/completions > pr_notes.txt; \
		echo "Pull request notes generated."; \
		if [ "$$LOG_LEVEL" = "DEBUG" ]; then \
			echo "Pull request notes content:"; \
			cat pr_notes.txt; \
		fi; \
		echo "Pull request notes content:"; \
		cat pr_notes.txt; \
		git push origin $$current_branch; \
	fi
