vllm serve Mistral-7B-Instruct-Raft-Wifi \
    --enable-auto-tool-choice \
    --tool-call-parser mistral \
    --port 8002