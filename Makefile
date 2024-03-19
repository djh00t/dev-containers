USERNAME := $(shell whoami)
TIMESTAMP := $(shell date +%Y%m%d%H%M%S)
BRANCH_NAME := $(USERNAME)-$(TIMESTAMP)

.PHONY: clean branch push

clean:
	@git clean -fdx

branch:
	@git checkout -b $(BRANCH_NAME)

push:
	@git diff --name-only main...$(BRANCH_NAME) | xargs -I {} git diff main...$(BRANCH_NAME) -- {} | curl -X POST -H "Content-Type: text/plain" --data-binary @- https://api.openai.com/v1/engines/text-davinci-003/completions -d '{"prompt": "Create a bullet pointed change log for the following diffs:\n\n", "temperature": 0.7}' > changelog.txt
	@git tag -a $(BRANCH_NAME) -m "Release $(BRANCH_NAME)"
	@git push origin $(BRANCH_NAME) --tags
