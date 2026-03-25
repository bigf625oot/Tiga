import os

matches = []
for r, d, files in os.walk('d:/Tiga/backend/app/services/eah_agent'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(r, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                if 'app.services.eah_agent.core.agent_' in content or 'app.services.eah_agent.core' in content:
                    matches.append(path)

print("MATCHES:", matches)
