import sys
sys.path.insert(0, r'd:\Tiga\backend')
import importlib
import traceback

modules = [
    'app.api.endpoints.knowledge',
    'app.services.intelligence.knowledge.rag.knowledge_base',
    'app.services.intelligence.knowledge.extractor.document_parser'
]

with open('verify_log.txt', 'w') as f:
    for m in modules:
        try:
            importlib.import_module(m)
            f.write(f'{m} OK\n')
        except Exception as e:
            f.write(f'{m} FAILED: {e}\n')
            f.write(traceback.format_exc() + '\n')
