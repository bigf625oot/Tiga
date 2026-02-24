import logging
from typing import Dict, Any, Optional
from app.services.sandbox.e2b_sandbox import E2BSandboxService

logger = logging.getLogger(__name__)

# Replace the local CodeBoxSandbox with E2BSandboxService
# We keep the name 'codebox_service' to avoid breaking imports in other files
codebox_service = E2BSandboxService()
