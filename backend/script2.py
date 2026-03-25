import sys
try:
    import pygit2
    repo = pygit2.Repository('.')
    commit = repo.revparse_single('HEAD^')
    tree = commit.tree
    entry = tree['app/services/eah_agent/core/agent_nlu.py']
    blob = repo[entry.id]
    with open('app/services/eah_agent/orchestration/nlu.py', 'wb') as f:
        f.write(blob.data)
except Exception as e:
    print(e)
