# UpdatingDelegates

A set of Python utilities for managing Camunda BPMN processes, specifically focusing on Java delegates and output parameter mapping.

## Script

## `update_outputparameters.py`
Updates output parameter references in BPMN processes based on a mapping defined in a CSV file. It dynamically extracts XML namespaces and ensures correct XML declaration formatting.

#### Usage:
```bash
python update_outputparameters.py --csv <path_to_csv> [--bpmn-dir <directory> | --url <camunda_engine_rest_url>] [--overwrite | --deploy] [--bearer-token <token>] [--ignore-cert]
```

#### Example (Directory - Dry Run):
```bash
python update_outputparameters.py --csv DelegatesOutputParams.csv --bpmn-dir ./test_bpmn_dir
```

#### Example (Directory - Overwrite):
```bash
python update_outputparameters.py --csv DelegatesOutputParams.csv --bpmn-dir ./test_bpmn_dir --overwrite
```

#### Example (URL - Dry Run):
```bash
python update_outputparameters.py --csv DelegatesOutputParams.csv --url http://localhost:8080/engine-rest --bearer-token <specific-token> --ignore-cert
```

#### Example (URL - Deploy):
```bash
python update_outputparameters.py --csv DelegatesOutputParams.csv --url http://localhost:8080/engine-rest --deploy --bearer-token <specific-token>
```

## CSV Format
The `DelegatesOutputParams.csv` file should contain at least the following headers:
- `DelegateClass`: The Java delegate class or expression.
- `OutputParam`: The output parameter name to map.
