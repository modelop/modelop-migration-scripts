import os
import re

SEARCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlc-building-blocks")

OLD_IMPORT = "import org.apache.commons.lang.text.StrSubstitutor"
NEW_IMPORT = "import org.apache.commons.text.StringSubstitutor"

OLD_CLASS = "StrSubstitutor"
NEW_CLASS = "StringSubstitutor"

def main():
    modified_files = []
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

            modified_files.append(fname)

    print(f"\nModified {len(modified_files)} file(s):")
    for f in modified_files:
        print(f"  - {f}")

if __name__ == "__main__":
    main()
