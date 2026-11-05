.PHONY: ingest test eval demo serve
ingest: ; python -m knowledge_assistant ingest
test: ; python -m pytest -q
eval: ; python -m knowledge_assistant eval --provider $${PROVIDER:-mock}
demo: ; python -m knowledge_assistant ask "What is the supervisor approval threshold for refunds?" && python -m knowledge_assistant ask "What are the executive compensation bands?" && python -m knowledge_assistant ask "What are the executive compensation bands?" --role hr
serve: ; python -m knowledge_assistant serve --port 8081
