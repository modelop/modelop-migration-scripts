# fix_strsubstitutor.py

Replaces deprecated `org.apache.commons.lang.text.StrSubstitutor` usages with
`org.apache.commons.text.StringSubstitutor` inside BPMN files — either on
disk, or fetched live from a running Camunda instance.

Specifically, for any file/process containing the import:

```java
import org.apache.commons.lang.text.StrSubstitutor
```

it rewrites the import to:

```java
import org.apache.commons.text.StringSubstitutor
```

and renames all `StrSubstitutor` references to `StringSubstitutor`.

## Requirements

```bash
pip install requests
```

## Modes

The script supports two independent modes, `--bpmn-dir` and `--url`. At
least one must be provided; both may be used in the same run.

### 1. Local filesystem mode (`--bpmn-dir`)

Recursively scans a directory for `.bpmn` files and patches any that contain
the deprecated import.

```bash
python3 fix_strsubstitutor.py --bpmn-dir ./mlc-building-blocks --overwrite
```

- Without `--overwrite`, it's a dry run: it reports which files *would* be
  changed without writing anything.
- With `--overwrite`, matching files are rewritten in place.

### 2. Camunda REST API mode (`--url`)

Fetches the latest version of every deployed process definition directly
from a Camunda Engine REST API, patches the XML in memory, and optionally
redeploys the changed ones — using each process's original name and key as
found in Camunda.

```bash
python3 fix_strsubstitutor.py \
  --url http://localhost:8090/mlc-service/rest \
  --deploy \
  --bearer-token <your-token> \
  --ignore-cert
```

- `--url` — base URL of the Camunda REST API (e.g.
  `http://localhost:8080/engine-rest`, or a gateway-routed path such as
  `http://localhost:8090/mlc-service/rest`).
- `--deploy` — without it, it's a dry run: it reports which process
  definitions *would* be redeployed without pushing anything. With it,
  changed definitions are deployed back to Camunda.
- `--bearer-token` — bearer token sent as `Authorization: Bearer <token>`.
- `--ignore-cert` — skip TLS certificate verification (self-signed certs).

## Examples

Dry run over a local checkout, no changes written:

```bash
python3 fix_strsubstitutor.py --bpmn-dir ./mlc-building-blocks
```

Fix and overwrite local files:

```bash
python3 fix_strsubstitutor.py --bpmn-dir ./mlc-building-blocks --overwrite
```

Check what's deployed in Camunda without changing anything:

```bash
python3 fix_strsubstitutor.py --url http://localhost:8090/mlc-service/rest --bearer-token <token>
```

Fix and redeploy affected processes in Camunda:

```bash
python3 fix_strsubstitutor.py \
  --url http://localhost:8090/mlc-service/rest \
  --deploy \
  --bearer-token <token> \
  --ignore-cert
```
