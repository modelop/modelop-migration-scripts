# UpdatingDelegates

A set of Python utilities for managing Camunda BPMN processes, specifically focusing on Java delegates and output parameter mapping, plus fixing deprecated `StrSubstitutor` imports in scripts.

## Script

## `update_outputparameters.py`
Updates output parameter references in BPMN processes based on a mapping defined in a CSV file. It dynamically extracts XML namespaces and ensures correct XML declaration formatting.

In the same pass it also replaces deprecated `StrSubstitutor` usages in scripts (script tasks, `camunda:script` blocks, listeners, etc.). For any script containing:

```java
import org.apache.commons.lang.text.StrSubstitutor
```

it rewrites the import to:

```java
import org.apache.commons.text.StringSubstitutor
```

and renames all `StrSubstitutor` references in that script to `StringSubstitutor`.

When a process is modified by either change, the script also:
- Sets the process `camunda:versionTag` to `3.5-1` (only if the existing tag matches a numeric version pattern such as `1.0` or `3.4-2`, or is missing).
- Appends a `Release Notes:` entry to the process `<bpmn:documentation>` (creating it if missing) for each change that was applied:
  - `- 3.5-1 MOC-130 Explicit Output Global Variables` — output parameters were added.
  - `- 3.5-1 Replaced deprecated StrSubstitutor with StringSubstitutor` — StrSubstitutor imports were fixed.
- When using `--url --deploy`, re-suspends processes that were suspended before redeployment.

No third-party packages are required (standard library only).

#### Usage:
```bash
python update_outputparameters.py --csv <path_to_csv> [--bpmn-dir <directory> | --url <camunda_engine_rest_url>] [--overwrite | --deploy] [--bearer-token <token>] [--ignore-cert]
```

#### Optional Arguments:

- **-h, --help**: Show this help message and exit.
- **--bpmn-dir `BPMN_DIR`**: Directory to search recursively for .bpmn files (e.g., `./BPMNs` or a repo root). Either this or `--url` must be provided.
- **--csv `CSV_PATH`**: Path to `DelegatesOutputParams.csv` (default: `DelegatesOutputParams.csv`). The CSV must exist even if you only need the StrSubstitutor fix.
- **--url `URL`**: Base URL of the Camunda Engine REST API (e.g., `http://localhost:8090/mlc-service/rest`). Either this or `--bpmn-dir` must be provided.
- **--deploy**: If set when using `--url`, automatically deploy the modified XMLs back to Camunda. Otherwise acts as a dry-run.
- **--overwrite**: If set when using `--bpmn-dir`, automatically overwrite the modified XML files locally. Otherwise acts as a dry-run.
- **--bearer-token `BEARER_TOKEN`**: Optional Bearer token for authorization when using `--url`.
- **--ignore-cert**: If set when using `--url`, ignore SSL certificate errors.

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
python update_outputparameters.py --csv DelegatesOutputParams.csv --url http://localhost:8090/mlc-service/rest --bearer-token <specific-token> --ignore-cert
```

#### Example (URL - Deploy):
```bash
python update_outputparameters.py --csv DelegatesOutputParams.csv --url http://localhost:8090/mlc-service/rest --deploy --bearer-token <specific-token>
```

## CSV Format
The `DelegatesOutputParams.csv` file should contain at least the following headers:
- `DelegateClass`: The Java delegate class or expression.
- `OutputParam`: The output parameter name to map.
