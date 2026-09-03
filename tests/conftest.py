import os
import sys

# pytest imports this file before collecting the tests, so every test module can
# import from the two folders below without repeating the boilerplate itself.
# The paths are relative, so the suite has to be run from the repository root.
sys.path.append('./modules')
sys.path.append('./tests/files')

# Wait for the vscode debugger to attach. See the "Debug with vscode" section of the README.
if os.environ.get('DEBUG') == 'true':
    import debugpy
    # Without this, pytest's parse.py subprocesses are debugged too, and each waits for
    # the debugger on a port the container does not publish, which stalls the whole run.
    debugpy.configure(subProcess=False)
    debugpy.listen(('0.0.0.0', 3000))
    debugpy.wait_for_client()
