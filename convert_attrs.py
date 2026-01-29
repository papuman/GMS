#!/usr/bin/env python3
"""Convert Odoo 17 attrs= syntax to Odoo 19 direct attributes"""
import re
import sys

def convert_domain_to_python(domain_str):
    """Convert Odoo domain to Python expression"""
    # Remove quotes around domain
    domain_str = domain_str.strip()

    # Handle simple cases
    conversions = {
        # Single conditions
        r"\('(\w+)', '=', False\)": r"not \1",
        r"\('(\w+)', '!=', False\)": r"\1",
        r"\('(\w+)', '=', True\)": r"\1",
        r"\('(\w+)', '!=', True\)": r"not \1",
        r"\('(\w+)', '=', '([^']+)'\)": r"\1 == '\2'",
        r"\('(\w+)', '!=', '([^']+)'\)": r"\1 != '\2'",
        r"\('(\w+)', '=', (\d+)\)": r"\1 == \2",
        r"\('(\w+)', '!=', (\d+)\)": r"\1 != \2",
        r"\('(\w+)', '>', (\d+)\)": r"\1 > \2",
        r"\('(\w+)', '<', (\d+)\)": r"\1 < \2",
        r"\('(\w+)', '>=', (\d+)\)": r"\1 >= \2",
        r"\('(\w+)', '<=', (\d+)\)": r"\1 <= \2",
    }

    result = domain_str
    for pattern, replacement in conversions.items():
        result = re.sub(pattern, replacement, result)

    # Handle OR operator ('|')
    result = result.replace("'|',", "")
    result = result.replace(", '|'", "")

    # Handle list notation
    result = re.sub(r'\[([^\]]+)\]', r'\1', result)

    # Handle AND (multiple conditions without |)
    if ',' in result and 'or' not in result:
        parts = [p.strip() for p in result.split(',') if p.strip()]
        result = ' and '.join(parts)

    # Handle OR
    if '|' not in domain_str and 'or' not in result and len([p for p in result.split(',') if p.strip()]) == 2:
        # Might be OR
        pass

    return result.strip()

def convert_attrs_line(line):
    """Convert a single line with attrs= to direct attribute"""

    # Pattern: attrs="{'invisible': [...]}"
    invisible_match = re.search(r'''attrs=["']({'invisible':\s*\[([^\]]+)\]})["']''', line)
    if invisible_match:
        domain = invisible_match.group(2)
        python_expr = convert_domain_to_python(domain)
        # Replace attrs= with invisible=
        new_line = re.sub(r'''attrs=["']{'invisible':\s*\[[^\]]+\]}["']''',
                         f'invisible="{python_expr}"', line)
        return new_line

    # Pattern: attrs="{'required': [...]}"
    required_match = re.search(r'''attrs=["']({'required':\s*\[([^\]]+)\]})["']''', line)
    if required_match:
        domain = required_match.group(2)
        python_expr = convert_domain_to_python(domain)
        new_line = re.sub(r'''attrs=["']{'required':\s*\[[^\]]+\]}["']''',
                         f'required="{python_expr}"', line)
        return new_line

    # Pattern: attrs="{'readonly': [...]}"
    readonly_match = re.search(r'''attrs=["']({'readonly':\s*\[([^\]]+)\]})["']''', line)
    if readonly_match:
        domain = readonly_match.group(2)
        python_expr = convert_domain_to_python(domain)
        new_line = re.sub(r'''attrs=["']{'readonly':\s*\[[^\]]+\]}["']''',
                         f'readonly="{python_expr}"', line)
        return new_line

    return line

def convert_file(filepath):
    """Convert attrs in a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if 'attrs=' in line:
            new_line = convert_attrs_line(line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Converted: {filepath}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 convert_attrs.py <file1.xml> <file2.xml> ...")
        sys.exit(1)

    for filepath in sys.argv[1:]:
        convert_file(filepath)
