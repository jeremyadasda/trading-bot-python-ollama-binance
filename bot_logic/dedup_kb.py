import os

def deduplicate_kb():
    kb_path = r"c:\Users\pepez\Desktop\trading-bot-ia\bot_logic\knowledge_base.md"
    if not os.path.exists(kb_path):
        return

    with open(kb_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    unique_lines = []
    seen_rules = set()
    
    in_dynamic_section = False
    
    for line in lines:
        if "## 4. Auto-Learned Insights" in line:
            in_dynamic_section = True
            unique_lines.append(line)
            continue
            
        if in_dynamic_section:
            # Check if it's a rule line (starts with - ** or * **)
            clean_line = line.strip()
            if (clean_line.startswith("- **") or clean_line.startswith("* **")) and "[Auto-Learned" in clean_line:
                # Extract the core rule text (ignoring the date tag)
                rule_text = clean_line.split("]:**")[-1].strip() if "]:**" in clean_line else clean_line
                if rule_text not in seen_rules:
                    seen_rules.add(rule_text)
                    unique_lines.append(line)
            elif clean_line == "" or not (clean_line.startswith("-") or clean_line.startswith("*")):
                # Keep empty lines or descriptive text for the LAST unique rule
                unique_lines.append(line)
            else:
                # Possible duplicate or non-rule but bulleted line
                if clean_line not in seen_rules:
                    seen_rules.add(clean_line)
                    unique_lines.append(line)
        else:
            unique_lines.append(line)

    with open(kb_path, 'w', encoding='utf-8') as f:
        f.writelines(unique_lines)
    print("KB Deduplicated.")

if __name__ == "__main__":
    deduplicate_kb()
