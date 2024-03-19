USERNAME := $(shell whoami)
TIMESTAMP := $(shell date +%Y%m%d%H%M%S)
BRANCH_NAME := $(USERNAME)-$(TIMESTAMP)

.PHONY: clean branch push

clean:
	@git clean -fdx

branch:
	@git checkout -b $(BRANCH_NAME)

push:
	@git diff --name-only main...$(BRANCH_NAME) | xargs -I {} git diff main...$(BRANCH_NAME) -- {} | curl -X POST -H "Content-Type: text/plain" --data-binary @- https://api.openai.com/v1/engines/text-davinci-003/completions -d '{"prompt": "You are an expert software engineer.\nReview the provided context and diffs which are about to be committed to a git repo.\nGenerate a *SHORT* 1 line, 1 sentence commit message per change that describes the purpose of the changes.\nEach commit message MUST be in the past tense.\nIt must describe the changes *which have been made* in the diffs!\nReply with JUST the commit message, without quotes, comments, questions, etc!", "temperature": 0.7}' > changelog.txt
	@git tag -a $(BRANCH_NAME) -m "Release $(BRANCH_NAME)"
	@git push origin $(BRANCH_NAME) --tags
