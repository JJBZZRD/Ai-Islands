# Ai-Islands

## Known Issues

### Transformer model - Reranker Model
Reranker model "jinaai/jina-reranker-v2-base-multilingual" requires `trust_remote_code=True` in order to work. 
During download and loading phases, it will need to run some remote code on the local computer in a child process 
(this is the action set by the model developer and thus cannot be changed). 
However, this behaviour leads to an unexpected error with fastapi development mode. 
This issue occurs ONLY in development mode but not in production mode. 
Thus, it works with `fastapi run backend/api/main.py` but not with `fastapi dev backend/api/main.py`. 
Ben: I have tried so many ways to fix the issue but it just could not work with fastapi dev. 
Good news is that it works fine with fastapi run somehow :).
