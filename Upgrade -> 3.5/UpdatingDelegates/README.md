# UpdatingDelegates

A set of Python utilities for auditing and managing Camunda BPMN processes, specifically focusing on Java delegates and output parameter mapping.

## Scripts

### `find_delegate.py`
Searches for specific Java delegates, classes, or expressions used in BPMN Service Tasks.

#### Usage:
```bash
python find_delegate.py --delegate <delegate_name> [--bpmn-dir <directory> | --url <camunda_engine_rest_url>]
```

### `update_outputparameters.py`
Audits and updates output parameter references in BPMN processes based on a mapping defined in a CSV file. It now dynamically extracts XML namespaces and ensures correct XML declaration formatting.

#### Usage:
```bash
python update_outputparameters.py --csv <path_to_csv> [--bpmn-dir <directory> | --url <camunda_engine_rest_url>] [--overwrite | --deploy] [--bearer-token <token>]
```

## CSV Format
The `DelegatesOutputParams.csv` file should contain at least the following headers:
- `DelegateClass`: The Java delegate class or expression.
- `OutputParam`: The output parameter name to map.
