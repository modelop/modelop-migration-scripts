import argparse
from pathlib import Path
from typing import Dict, List, Optional

import requests

OLD_IMPORT = "import org.apache.commons.lang.text.StrSubstitutor"
NEW_IMPORT = "import org.apache.commons.text.StringSubstitutor"

OLD_CLASS = "StrSubstitutor"
NEW_CLASS = "StringSubstitutor"


def fix_content(content: str) -> (str, bool):
    """Replace deprecated StrSubstitutor usages in a BPMN XML string."""
    if OLD_IMPORT not in content:
        return content, False

    new_content = content.replace(OLD_IMPORT, NEW_IMPORT)
    new_content = new_content.replace(OLD_CLASS, NEW_CLASS)
    return new_content, True


# Local filesystem mode

def process_bpmn_dir(bpmn_dir: Path, overwrite: bool) -> List[Path]:
    bpmn_files = sorted(p for p in bpmn_dir.rglob("*.bpmn") if p.is_file())
    if not bpmn_files:
        raise SystemExit(f"No .bpmn files found under {bpmn_dir}")

    changed_files = []
    for file in bpmn_files:
        content = file.read_text(encoding="utf-8")
        new_content, changed = fix_content(content)
        if not changed:
            continue

        changed_files.append(file)
        if overwrite:
            file.write_text(new_content, encoding="utf-8")
            print(f"Updated: {file}")
        else:
            print(f"Would update (dry run): {file}. Use --overwrite to save changes.")

    return changed_files


# Camunda REST API mode

def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def get_process_definitions(base_url: str, token: Optional[str], verify: bool) -> List[Dict]:
    url = f"{base_url.rstrip('/')}/process-definition?latestVersion=true"
    resp = requests.get(url, headers=_auth_headers(token), verify=verify)
    resp.raise_for_status()
    return resp.json()


def get_process_definition_xml(base_url: str, pd_id: str, token: Optional[str], verify: bool) -> Optional[str]:
    url = f"{base_url.rstrip('/')}/process-definition/{pd_id}/xml"
    resp = requests.get(url, headers=_auth_headers(token), verify=verify)
    resp.raise_for_status()
    return resp.json().get("bpmn20Xml")


def deploy_to_camunda(base_url: str, deployment_name: str, xml_content: str, filename: str,
                       token: Optional[str], verify: bool) -> bool:
    url = f"{base_url.rstrip('/')}/deployment/create"
    data = {
        "deployment-name": deployment_name,
        "enable-duplicate-filtering": "true",
        "deploy-changed-only": "true",
    }
    files = {filename: (filename, xml_content.encode("utf-8"), "text/xml")}

    resp = requests.post(url, headers=_auth_headers(token), data=data, files=files, verify=verify)
    if resp.ok:
        print(f"Successfully deployed: {deployment_name}")
        return True

    print(f"Failed to deploy {deployment_name}: {resp.status_code} {resp.text}")
    return False


def process_camunda(base_url: str, deploy: bool, token: Optional[str], verify: bool) -> List[str]:
    print(f"Connecting to Camunda at {base_url}")
    process_defs = get_process_definitions(base_url, token, verify)
    if not process_defs:
        print("No process definitions found or failed to connect.")
        return []

    print(f"Found {len(process_defs)} process definitions. Checking for necessary updates...")

    changed_keys = []
    for pdef in process_defs:
        pd_id = pdef.get("id")
        pd_key = pdef.get("key")
        pd_name = pdef.get("name") or pd_key

        xml_content = get_process_definition_xml(base_url, pd_id, token, verify)
        if not xml_content:
            continue

        print(f"Analyzing process: {pd_key} [{pd_id}]")
        new_xml, changed = fix_content(xml_content)
        if not changed:
            print(f"No changes required for process {pd_key}.\n")
            continue

        changed_keys.append(pd_key)
        print(f"Analysis found that Process {pd_key} requires updates.")

        if deploy:
            deploy_to_camunda(
                base_url, pd_name, new_xml, f"{pd_key}.bpmn", token, verify
            )
        else:
            print(f"Dry run. Skipping deployment for {pd_key}. Use --deploy to push changes.\n")

    return changed_keys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace deprecated StrSubstitutor usages in BPMN files, "
                     "either on disk or fetched live from a Camunda REST API."
    )
    parser.add_argument(
        "--bpmn-dir",
        help="Directory to search recursively for .bpmn files. Either this or --url must be provided.",
    )
    parser.add_argument(
        "--url",
        help="Base URL of the Camunda Engine REST API (e.g., http://localhost:8080/engine-rest). "
             "Either this or --bpmn-dir must be provided.",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="If set when using --bpmn-dir, automatically overwrite the modified XML files locally. "
             "Otherwise acts as a dry-run.",
    )
    parser.add_argument(
        "--deploy", action="store_true",
        help="If set when using --url, automatically deploy the modified XMLs back to Camunda. "
             "Otherwise acts as a dry-run.",
    )
    parser.add_argument(
        "--bearer-token",
        help="Bearer token for authorization when using --url.",
    )
    parser.add_argument(
        "--ignore-cert", action="store_true",
        help="If set when using --url, ignore SSL certificate errors.",
    )
    args = parser.parse_args()

    if not args.bpmn_dir and not args.url:
        parser.error("Either --bpmn-dir or --url must be provided.")

    if args.ignore_cert:
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    if args.url:
        changed_keys = process_camunda(
            args.url, deploy=args.deploy, token=args.bearer_token, verify=not args.ignore_cert
        )
        print(f"\nDone. {len(changed_keys)} process(es) required updates.")

    if args.bpmn_dir:
        bpmn_dir = Path(args.bpmn_dir).expanduser().resolve()
        if not bpmn_dir.exists() or not bpmn_dir.is_dir():
            raise SystemExit(f"BPMN directory not found or not a directory: {bpmn_dir}")

        changed_files = process_bpmn_dir(bpmn_dir, overwrite=args.overwrite)
        print(f"\nDone. Modified {len(changed_files)} file(s):")
        for f in changed_files:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
