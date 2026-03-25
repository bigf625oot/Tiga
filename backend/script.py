import subprocess
import os

out = subprocess.check_output(
    ['git', '--no-pager', 'show', 'HEAD^:app/services/eah_agent/core/agent_nlu.py'],
    cwd='d:/Tiga/backend',
    env=dict(os.environ, GIT_PAGER='cat')
)

with open('d:/Tiga/backend/app/services/eah_agent/orchestration/nlu.py', 'wb') as f:
    f.write(out)
