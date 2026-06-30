# mneme

The user-facing SDK for mneme-memory. Two modes, one API:

```python
from mneme import Mneme

# Embedded mode — no server needed, runs in-process
mneme = Mneme.embed()
mneme.retain("User is a Python developer")
results = mneme.recall("What's the user's background?")

# Remote mode — connect to a running mneme-server
mneme = Mneme.connect("http://localhost:9177")
mneme.retain("User is a Python developer")
results = mneme.recall("What's the user's background?")
```

## Installation

```bash
# Embedded mode (all-in-one, no server required)
pip install mneme

# With server support
pip install "mneme[server]"
```
