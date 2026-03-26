import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.parse
import json

CAMUNDA_NS = "http://camunda.org/schema/1.0/bpmn"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"

NS = {
    "bpmn": BPMN_NS,
    "camunda": CAMUNDA_NS,
}

ET.register_namespace("bpmn", BPMN_NS)
ET.register_namespace("camunda", CAMUNDA_NS)

def _lowercase_first_char(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return s
    return s[0].lower() + s[1:]

def get_camunda_process_definitions(base_url: str, token: Optional[str] = None) -> List[Dict]:
    """Fetch the latest version of all deployed process definitions."""
    url = f"{base_url.rstrip('/')}/process-definition?latestVersion=true"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = response.read()
                return json.loads(data)
            else:
                print(f"Error fetching process definitions: HTTP {response.status}")
                return []
    except Exception as e:
        print(f"Error connecting to Camunda at {url}: {e}")
        return []


def get_camunda_bpmn_xml(base_url: str, process_definition_id: str, token: Optional[str] = None) -> Optional[str]:
    """Fetch the BPMN XML string for a specific process definition."""
    url = f"{base_url.rstrip('/')}/process-definition/{urllib.parse.quote(process_definition_id)}/xml"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read())
                return data.get("bpmn20Xml")
            else:
                print(f"Error fetching XML for {process_definition_id}: HTTP {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching XML for {process_definition_id}: {e}")
        return None


def search_bpmn_tree_for_delegate(tree: ET.ElementTree, delegate_name: str) -> List[Tuple[str, str]]:
    """Search a parsed XML tree for a service task using the specified delegate name."""
    root = tree.getroot()
    found_tasks = []

    for st in root.findall(".//bpmn:serviceTask", namespaces=NS):
        delegate_expr = st.get(f"{{{CAMUNDA_NS}}}delegateExpression") or ""
        camunda_class = st.get(f"{{{CAMUNDA_NS}}}class") or ""
        camunda_expr = st.get(f"{{{CAMUNDA_NS}}}expression") or ""

        match = False
        if _lowercase_first_char(delegate_name) in delegate_expr or delegate_name in camunda_class or delegate_name in camunda_expr:
            match = True

        if match:
            task_id = st.get("id", "unknown_id")
            task_name = st.get("name", "unnamed_task")
            found_tasks.append((task_id, task_name))

    return found_tasks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find BPMN files containing a specific delegate within a service task."
    )
    parser.add_argument(
        "--bpmn-dir",
        help="Directory to search recursively for .bpmn files (e.g., ./BPMNs or a repo root). Either this or --url must be provided.",
    )
    parser.add_argument(
        "--url",
        help="Base URL of the Camunda Engine REST API (e.g., http://localhost:8080/engine-rest). Either this or --bpmn-dir must be provided.",
    )
    parser.add_argument(
        "--bearer-token",
        help="Optional Bearer token for authorization when using --url.",
    )
    parser.add_argument(
        "--delegate",
        required=True,
        help="The specific delegate name, class, or expression to search for.",
    )
    
    args = parser.parse_args()

    if not args.bpmn_dir and not args.url:
        parser.error("Either --bpmn-dir or --url must be provided.")

    print(f"\nSearching for '{args.delegate}'...")
    
    total_matches = 0

    if args.url:
        print(f"\nConnecting to Camunda at {args.url}")
        process_defs = get_camunda_process_definitions(args.url, token=args.bearer_token)
        if not process_defs:
            print("No process definitions found or failed to connect.")
            return
            
        print(f"Found {len(process_defs)} process definitions. Searching for delegate...")
        
        for pdef in process_defs:
            pd_id = pdef.get("id")
            pd_key = pdef.get("key")
            pd_name = pdef.get("name") or pd_key
            
            xml_content = get_camunda_bpmn_xml(args.url, pd_id, token=args.bearer_token)
            if not xml_content:
                continue
                
            try:
                tree = ET.ElementTree(ET.fromstring(xml_content))
                matches = search_bpmn_tree_for_delegate(tree, args.delegate)
                if matches:
                    total_matches += 1
                    print(f"\nProcess Definition: {pd_key} [{pd_id}]")
                    for task_id, task_name in matches:
                        print(f"   └── Task ID: {task_id} | Name: {task_name}")
                    
            except ET.ParseError as e:
                print(f"Error parsing XML for {pd_id}: {e}\n")
            except Exception as e:
                import traceback
                print(f"Error processing {pd_id}: {e}\n")
                traceback.print_exc()

    if args.bpmn_dir:
        bpmn_dir = Path(args.bpmn_dir).expanduser().resolve()
        if not bpmn_dir.exists() or not bpmn_dir.is_dir():
            raise SystemExit(f"BPMN directory not found or not a directory: {bpmn_dir}")

        bpmn_files = sorted(p for p in bpmn_dir.rglob("*.bpmn") if p.is_file())
        if not bpmn_files:
            raise SystemExit(f"No .bpmn files found under {bpmn_dir}")

        print(f"\nSearching local directory: {bpmn_dir}")
        for filepath in bpmn_files:
            try:
                tree = ET.parse(filepath)
                matches = search_bpmn_tree_for_delegate(tree, args.delegate)
                if matches:
                    total_matches += 1
                    print(f"\n{filepath}")
                    for task_id, task_name in matches:
                        print(f"   └── Task ID: {task_id} | Name: {task_name}")
                        
            except ET.ParseError as e:
                print(f"Error parsing XML for {filepath}: {e}\n")
            except Exception as e:
                print(f"Error processing {filepath}: {e}\n")

    if total_matches:
        print(f"\nTotal files/processes matched: {total_matches}")
    else:
        print(f"\nNo Service Tasks found using delegate '{args.delegate}'.")


if __name__ == "__main__":
    main()
