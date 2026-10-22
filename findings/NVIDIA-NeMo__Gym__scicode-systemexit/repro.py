# run from the repo root, with resources_servers/scicode on PYTHONPATH
import sys
from resources_servers.scicode.scicode_integration.runner import run_substep

# A sub-step program whose only test is `assert False`, preceded by the "solution" `raise SystemExit(0)`.
program = "raise SystemExit(0)\n\nassert False, 'tests must not pass'\n"
print(run_substep(program, timeout_secs=30, python_executable=sys.executable))
