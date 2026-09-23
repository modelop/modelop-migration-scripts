import argparse
import os
import re

import requests

SEARCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlc-building-blocks")

OLD_IMPORT = "import org.apache.commons.lang.text.StrSubstitutor"
NEW_IMPORT = "import org.apache.commons.text.StringSubstitutor"

OLD_CLASS = "StrSubstitutor"
NEW_CLASS = "StringSubstitutor"


def fix_bpmns():
    """Walk SEARCH_DIR, patch matching .bpmn files in place, return their full paths."""
    modified_paths = []
    for root, dirs, files in os.walk(SEARCH_DIR):
        for fname in files:
            if not fname.endswith(".bpmn"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            if OLD_IMPORT not in content:
                continue

            print(f"Found: {fname}")

            new_content = content.replace(OLD_IMPORT, NEW_IMPORT)

            new_content = new_content.replace(OLD_CLASS, NEW_CLASS)

            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)

            modified_paths.append(fpath)

    return modified_paths


def deploy_bpmns(base_url, token, bpmn_paths):
    """Deploy the given .bpmn files to a Camunda 7 REST API endpoint via bearer token auth."""
    url = f"{base_url.rstrip('/')}/mlc-service/rest/deployment/create"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "deployment-name": "fix_strsubstitutor",
        "deploy-changed-only": "true",
    }

    print(f"\nDeploying {len(bpmn_paths)} file(s) to {url}...")
    for fpath in bpmn_paths:
        fname = os.path.basename(fpath)
        with open(fpath, "rb") as f:
            files = {fname: (fname, f, "text/xml")}
            resp = requests.post(url, headers=headers, data=data, files=files)

        if resp.ok:
            print(f"  Deployed: {fname}")
        else:
            print(f"  Failed to deploy {fname}: {resp.status_code} {resp.text}")


def main():
    parser = argparse.ArgumentParser(
        description="Replace deprecated StrSubstitutor usages in .bpmn files, "
                     "optionally deploying the changed ones to Camunda."
    )
    parser.add_argument(
        "--deploy-url",
        help="Gateway base URL to deploy changed .bpmn files through; "
             "'/mlc-service/rest/deployment/create' is appended automatically "
             "(e.g. http://localhost:8090). If omitted, no deployment happens."
    )
    parser.add_argument(
        "--token",
        help="Bearer token used to authenticate against --deploy-url."
    )
    args = parser.parse_args()

    if bool(args.deploy_url) != bool(args.token):
        parser.error("--deploy-url and --token must be provided together")

    modified_paths = fix_bpmns()

    print(f"\nModified {len(modified_paths)} file(s):")
    for fpath in modified_paths:
        print(f"  - {os.path.basename(fpath)}")

    if args.deploy_url and modified_paths:
        deploy_bpmns(args.deploy_url, args.token, modified_paths)
    elif args.deploy_url:
        print("\nNo modified files to deploy.")


if __name__ == "__main__":
    main()
