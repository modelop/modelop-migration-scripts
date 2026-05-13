import argparse
from pathlib import Path
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import urllib.request
import urllib.parse
import json
import uuid

DEFAULT_CSV_PATH = Path("DelegatesOutputParams.csv")

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


def _normalize_delegate_expression(raw: str) -> str:
    s = (raw or "").strip()
    if s.startswith("${") and s.endswith("}"):
        s = s[2:-1].strip()
    return s


def _matches_output_reference(op: ET.Element, param: str):
    raw_value = (op.text or op.get("value") or "").strip()
    if (
            f"${{{param}}}" in raw_value
            or f'${{execution.getVariable("{param}")}}' in raw_value
            or f"${{execution.getVariable('{param}')}}" in raw_value
    ):
        return raw_value
    else:
        return None


def _matches_script_reference(op: ET.Element, param: str):
    script_elem = op.find("camunda:script", namespaces=NS)
    raw_script = script_elem.text if script_elem is not None else ""
    if (
        param in raw_script
        or f'execution.getVariable("{param}")' in raw_script
        or f"execution.getVariable('{param}')" in raw_script
    ):
        return raw_script.strip()
    else:
        return None


def _matches_remove_reference(op: ET.Element, param: str):
    raw_value = (op.text or op.get("value") or "").strip()
    if f"${{execution.removeVariable('{param}')}}" in raw_value:
        return raw_value
    script_elem = op.find("camunda:script", namespaces=NS)
    raw_script = script_elem.text if script_elem is not None else ""
    if (
        f'execution.removeVariable("{param}")' in raw_script
        or f"execution.removeVariable('{param}')" in raw_script
    ):
        return raw_script.strip()
    else:
        return None


def load_delegate_outputparam_map(csv_path: Path) -> Dict[str, List[str]]:
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path.resolve()}")

    mapping: Dict[str, List[str]] = {}

    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"CSV appears empty or has no header: {csv_path.resolve()}")

        fieldnames = [name.strip() for name in reader.fieldnames if name]
        name_map = {name.strip(): name for name in reader.fieldnames if name}

        if "DelegateClass" not in fieldnames or "OutputParam" not in fieldnames:
            raise SystemExit(
                "CSV must have headers 'DelegateClass' and 'OutputParam'. "
                f"Found: {reader.fieldnames}"
            )

        delegate_key = name_map["DelegateClass"]
        output_key = name_map["OutputParam"]

        for row in reader:
            delegate_raw = (row.get(delegate_key) or "").strip()
            out_param = (row.get(output_key) or "").strip()
            if not delegate_raw or not out_param:
                continue

            delegate = _lowercase_first_char(delegate_raw)

            current = mapping.setdefault(delegate, [])
            if out_param not in current:
                current.append(out_param)

    return mapping


def update_bpmn_tree(tree: ET.ElementTree, delegate_to_outputs: Dict[str, List[str]]) -> bool:
    root = tree.getroot()
    modified = False

    for st in root.findall(".//bpmn:serviceTask", namespaces=NS):
        delegate_expr = st.get(f"{{{CAMUNDA_NS}}}delegateExpression") or ""
        delegate_class = st.get(f"{{{CAMUNDA_NS}}}class") or ""
        
        # Determine the value to look up in the mapping
        if delegate_expr.strip():
            lookup_val = _lowercase_first_char(_normalize_delegate_expression(delegate_expr))
            log_msg = f"DelegateExpression: \"{lookup_val}\""
        elif delegate_class.strip():
            lookup_val = _lowercase_first_char(delegate_class.split('.')[-1])
            log_msg = f"Java Class: \"{lookup_val}\""
        else:
            continue

        outputs = delegate_to_outputs.get(lookup_val)
        st_id = st.get("id")
        task_name = (st.get('name') or "").replace('\n', ' ')
        print(f" |── Task Name: \"{task_name}\" | Servicetask ID: \"{st_id}\" | {log_msg}")
        if not outputs:
            continue

        ext = st.find("bpmn:extensionElements", namespaces=NS)
        if ext is None:
            ext = ET.SubElement(st, f"{{{BPMN_NS}}}extensionElements")

        cam_input_output = ext.find("camunda:inputOutput", namespaces=NS)
        if cam_input_output is None:
            cam_input_output = ET.SubElement(ext, f"{{{CAMUNDA_NS}}}inputOutput")

        existing = cam_input_output.findall("camunda:outputParameter", namespaces=NS)
        existing_names = {op.get("name") for op in existing if op.get("name")}

        # Swapping the outputs from the CSV file
        for out_param in outputs:
            # Looking for an existing output parameter with the same name
            if out_param in existing_names:
                print(f" |   Output parameter \"{out_param}\" already exists, skipping.")
                element_to_remove = next(
                    (op for op in existing if op.get("name") == out_param),
                    None,
                )
                script_elem = element_to_remove.find("camunda:script", namespaces=NS)
                existing_value = (
                    (script_elem.text if script_elem is not None else None)
                    or element_to_remove.text
                    or element_to_remove.get("value")
                    or ""
                ).replace('\n', ' ')
                print(f" |   Existing value: \"{existing_value}\"")
                existing.remove(element_to_remove)
                continue

            # Looking for any "removeVariable" references in the existing output parameters"
            remove_match = next((op for op in existing if _matches_remove_reference(op, out_param) is not None), None,)
            if remove_match is not None:
                existing_name = remove_match.get("name")
                print(f" |*- Output parameter \"{out_param}\" is being removed in parameter \"{existing_name}\", Make sure of not use this output parameter.")
                existing_value = _matches_remove_reference(remove_match, out_param).replace('\n', ' ')
                print(f" |   Existing value: \"{existing_value}\"")
                continue

            # Looking for the variable into the value/text of the existing output parameter
            value_match = next((op for op in existing if _matches_output_reference(op, out_param) is not None), None,)
            if value_match is not None:
                existing_name = value_match.get("name")
                print(f" |   Output parameter \"{out_param}\" already used in parameter \"{existing_name}\", skipping.")
                existing_value = _matches_output_reference(value_match, out_param).replace('\n', ' ')
                print(f" |   Existing value: \"{existing_value}\"")
                existing.remove(value_match)
                continue

            # Looking for the variable into the script text of the existing output parameter
            script_match = next((op for op in existing if _matches_script_reference(op, out_param)is not None), None,)
            if script_match is not None:
                existing_name = script_match.get("name")
                existing_script = _matches_script_reference(script_match, out_param).replace('\n', ' ')
                print(f" |*  Output parameter \"{out_param}\" already used in script \"{existing_name}\", skipping.")
                print(f" |   Existing script: \"{existing_script}\"")
                existing.remove(script_match)
                continue

            # When the variable is not found, we add the new output parameter
            outp = ET.SubElement(cam_input_output, f"{{{CAMUNDA_NS}}}outputParameter")
            outp.set("name", out_param)
            outp.set("value", f"${{execution.getVariable(\"{out_param}\")}}")
            print(f" |   Added output parameter: \"{out_param}\"")
            modified = True

        # Swapping the existing outputs in the ServiceTask
        for existing_output in existing:
            existing_output_name = (existing_output.get('name') or "").replace('\n', ' ')
            script_elem = existing_output.find("camunda:script", namespaces=NS)
            if script_elem is not None:
                script_text = (script_elem.text or "").replace('\n', ' ')
                print(f" |*  Keeping existing Output parameter name: \"{existing_output_name}\" with script: \"{script_text}\"")
            else:
                print(f" |*  Keeping existing Output parameter name: \"{existing_output_name}\" with value: \"{existing_output.text if existing_output.text is not None else existing_output.get('value')}\"")

    return modified


def add_output_parameters_from_csv(bpmn_path: Path, delegate_to_outputs: Dict[str, List[str]], overwrite: bool = False) -> bool:
    try:
        tree = ET.parse(bpmn_path)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in {bpmn_path}: {e}") from e

    modified = update_bpmn_tree(tree, delegate_to_outputs)
    
    if modified:
        if overwrite:
            print(f"Saving changes to {bpmn_path}")
            tree.write(bpmn_path, encoding="utf-8", xml_declaration=True)

    return modified


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


def deploy_to_camunda(base_url: str, deployment_name: str, xml_content: str, filename: str, token: Optional[str] = None) -> bool:
    """Deploy raw XML content to Camunda via multipart/form-data."""
    url = f"{base_url.rstrip('/')}/deployment/create"
    
    boundary = uuid.uuid4().hex
    
    # We build the multipart/form-data payload manually
    parts = []
    
    # Deployment name
    parts.append(f"--{boundary}\r\n")
    parts.append('Content-Disposition: form-data; name="deployment-name"\r\n\r\n')
    parts.append(deployment_name + "\r\n")
    
    # Enable duplicate filtering (optional but good practice)
    parts.append(f"--{boundary}\r\n")
    parts.append('Content-Disposition: form-data; name="enable-duplicate-filtering"\r\n\r\n')
    parts.append("true\r\n")
    
    # The actual XML file
    parts.append(f"--{boundary}\r\n")
    parts.append(f'Content-Disposition: form-data; name="data"; filename="{filename}"\r\n')
    parts.append('Content-Type: application/octet-stream\r\n\r\n')
    parts.append(xml_content + "\r\n")
    
    parts.append(f"--{boundary}--\r\n")
    
    body = "".join(parts).encode('utf-8')
    
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"Successfully deployed: {deployment_name}\n")
                return True
            else:
                print(f"Failed to deploy {deployment_name}: HTTP {response.status}\n")
                return False
    except Exception as e:
        print(f"Error deploying {deployment_name}: {e}\n")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add camunda:outputParameter entries to BPMN serviceTasks based on delegateExpression -> CSV mapping."
    )
    parser.add_argument(
        "--bpmn-dir",
        help="Directory to search recursively for .bpmn files (e.g., ./BPMNs or a repo root). Either this or --url must be provided.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=str(DEFAULT_CSV_PATH),
        help=f"Path to DelegatesOutputParams.csv (default: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--url",
        help="Base URL of the Camunda Engine REST API (e.g., http://localhost:8080/engine-rest). Either this or --bpmn-dir must be provided.",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="If set when using --url, automatically deploy the modified XMLs back to Camunda. Otherwise acts as a dry-run.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If set when using --bpmn-dir, automatically overwrite the modified XML files locally. Otherwise acts as a dry-run.",
    )
    parser.add_argument(
        "--bearer-token",
        help="Optional Bearer token for authorization when using --url.",
    )
    args = parser.parse_args()

    if not args.bpmn_dir and not args.url:
        parser.error("Either --bpmn-dir or --url must be provided.")

    csv_path = Path(args.csv_path).expanduser().resolve()
    delegate_to_outputs = load_delegate_outputparam_map(csv_path)

    changed = 0
    changed_files = []
    no_changed = 0
    no_changed_files = []
    error_count = 0
    error_files = []

    if args.url:
        print(f"Connecting to Camunda at {args.url}")
        process_defs = get_camunda_process_definitions(args.url, token=args.bearer_token)
        if not process_defs:
            print("No process definitions found or failed to connect.")
            return
            
        print(f"Found {len(process_defs)} process definitions. Checking for necessary updates...")
        
        for pdef in process_defs:
            pd_id = pdef.get("id")
            pd_key = pdef.get("key")
            pd_name = pdef.get("name") or pd_key
            
            xml_content = get_camunda_bpmn_xml(args.url, pd_id, token=args.bearer_token)
            if not xml_content:
                continue
                
            try:
                tree = ET.ElementTree(ET.fromstring(xml_content))
                
                print(f"Analyzing process: {pd_key} [{pd_id}]")
                if update_bpmn_tree(tree, delegate_to_outputs):
                    changed += 1
                    changed_files.append(pd_key)
                    print(f"Analysis found that Process {pd_key} requires updates.")
                    
                    if args.deploy:
                        # Convert back to string
                        ET.register_namespace("bpmn", BPMN_NS)
                        ET.register_namespace("camunda", CAMUNDA_NS)
                        xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)
                        xml_str = xml_bytes.decode("utf-8")
                        
                        deploy_name = f"{pd_name} (Updated)"
                        filename = f"{pd_key}.bpmn"
                        
                        deploy_to_camunda(args.url, deploy_name, xml_str, filename, token=args.bearer_token)
                    else:
                        print(f"Dry run. Skipping deployment for {pd_key}. Use --deploy to push changes.\n")
                else:
                    no_changed += 1
                    no_changed_files.append(pd_key)
                    print(f"No changes required for process {pd_key}.\n")
                    
            except ET.ParseError as e:
                error_count += 1
                error_files.append(pd_key)
                print(f"Error parsing XML for {pd_id}: {e}\n")
            except Exception as e:
                error_count += 1
                error_files.append(pd_key)
                import traceback
                print(f"Error processing {pd_id}: {e}\n")
                traceback.print_exc()
                
        print(
            f"Done. \n    Updates applicable to: {changed} Processes \n    No changes required for: {no_changed} Processes \n    Processes with errors: {error_count} \n    Total Processes analyzed: {len(process_defs)}")

    if args.bpmn_dir:
        bpmn_dir = Path(args.bpmn_dir).expanduser().resolve()
        if not bpmn_dir.exists() or not bpmn_dir.is_dir():
            raise SystemExit(f"BPMN directory not found or not a directory: {bpmn_dir}")

        bpmn_files = sorted(p for p in bpmn_dir.rglob("*.bpmn") if p.is_file())
        if not bpmn_files:
            raise SystemExit(f"No .bpmn files found under {bpmn_dir}")

        for file in bpmn_files:
            try:
                print(f"Analyzing file: {file}")
                if add_output_parameters_from_csv(file, delegate_to_outputs, args.overwrite):
                    changed += 1
                    changed_files.append(file.__str__())
                    if args.overwrite:
                        print(f"Updated: {file}\n")
                    else:
                        print(f"Would update (dry run): {file}.  Use --overwrite to save changes.\n")
                else:
                    no_changed += 1
                    no_changed_files.append(file.__str__())
                    print(f"No change required in file: {file}\n")
            except Exception as e:
                import traceback
                error_count += 1
                error_files.append(file.__str__())
                print(f"Error processing {file}: {type(e).__name__}: {e!r}\n")
                traceback.print_exc()

        print(f"Process Done. \n    Files changed: {changed} \n    Files unchanged: {no_changed} \n    Files with errors: {error_count} \n    Total files analyzed: {len(bpmn_files)}")

    if error_files:
        print("Files with errors:")
        for file in error_files:
            print(f"    - {file}")

if __name__ == "__main__":
    main()