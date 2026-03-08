#!/usr/bin/env python3

# ============================================================
# COMPARE DJANGO MODELS
# Parses two Django models.py files and generates a readable
# report of schema differences: tables, columns, foreign keys
#
# USAGE:
#   python compare_models.py <current_models.py> <new_models.py> <output_report.md>
#
# Called automatically by pre_merge_check.sh
# ============================================================

import ast
import sys
import os
from datetime import datetime


# ============================================================
# PARSER — extracts model info from a models.py file using AST
# AST (Abstract Syntax Tree) reads Python code as a structure
# without executing it — safe to use on any models.py file
# ============================================================

def parse_models(filepath):
    """
    Parses a Django models.py file and returns a dict like:
    {
      "ModelName": {
        "fields": {
          "field_name": "FieldType(args...)"
        },
        "foreign_keys": {
          "field_name": "RelatedModel"
        },
        "meta": { "db_table": "custom_table_name" }  # if defined
      }
    }
    """
    with open(filepath, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"  ERROR: could not parse {filepath}: {e}")
        sys.exit(1)

    models = {}

    for node in ast.walk(tree):
        # Find all classes that inherit from models.Model
        if isinstance(node, ast.ClassDef):
            bases = [
                (b.attr if isinstance(b, ast.Attribute) else b.id)
                for b in node.bases
                if isinstance(b, (ast.Attribute, ast.Name))
            ]
            if "Model" not in bases:
                continue

            model_name = node.name
            fields = {}
            foreign_keys = {}
            meta = {}

            for item in node.body:
                # Find field assignments like: name = models.CharField(...)
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        field_name = target.id
                        if field_name.startswith("_"):
                            continue

                        # Get field type and args
                        if isinstance(item.value, ast.Call):
                            func = item.value.func
                            if isinstance(func, ast.Attribute):
                                field_type = func.attr
                            elif isinstance(func, ast.Name):
                                field_type = func.id
                            else:
                                continue

                            # Skip non-field assignments
                            django_fields = [
                                "CharField", "TextField", "IntegerField", "FloatField",
                                "BooleanField", "DateField", "DateTimeField", "FileField",
                                "ImageField", "ForeignKey", "ManyToManyField", "OneToOneField",
                                "EmailField", "URLField", "SlugField", "UUIDField",
                                "AutoField", "BigAutoField", "JSONField", "DecimalField",
                                "PositiveIntegerField", "SmallIntegerField", "BigIntegerField",
                            ]
                            if field_type not in django_fields:
                                continue

                            # Get args as string for display
                            args = []
                            for arg in item.value.args:
                                if isinstance(arg, ast.Constant):
                                    args.append(repr(arg.value))
                                elif isinstance(arg, ast.Attribute):
                                    args.append(f"{arg.value.id}.{arg.attr}" if isinstance(arg.value, ast.Name) else arg.attr)
                                elif isinstance(arg, ast.Name):
                                    args.append(arg.id)

                            for kw in item.value.keywords:
                                if isinstance(kw.value, ast.Constant):
                                    args.append(f"{kw.arg}={repr(kw.value.value)}")
                                elif isinstance(kw.value, ast.Name):
                                    args.append(f"{kw.arg}={kw.value.id}")
                                elif isinstance(kw.value, ast.Attribute):
                                    args.append(f"{kw.arg}={kw.value.attr}")

                            field_str = f"{field_type}({', '.join(args)})"
                            fields[field_name] = field_str

                            # Track foreign keys separately
                            if field_type in ("ForeignKey", "ManyToManyField", "OneToOneField"):
                                related = None
                                if item.value.args:
                                    first_arg = item.value.args[0]
                                    if isinstance(first_arg, ast.Constant):
                                        related = first_arg.value
                                    elif isinstance(first_arg, ast.Name):
                                        related = first_arg.id
                                    elif isinstance(first_arg, ast.Attribute):
                                        related = first_arg.attr
                                foreign_keys[field_name] = f"{field_type} → {related or 'unknown'}"

                # Find Meta class for custom table names
                elif isinstance(item, ast.ClassDef) and item.name == "Meta":
                    for meta_item in item.body:
                        if isinstance(meta_item, ast.Assign):
                            for t in meta_item.targets:
                                if isinstance(t, ast.Name) and t.id == "db_table":
                                    if isinstance(meta_item.value, ast.Constant):
                                        meta["db_table"] = meta_item.value.value

            models[model_name] = {
                "fields": fields,
                "foreign_keys": foreign_keys,
                "meta": meta,
            }

    return models


# ============================================================
# COMPARATOR — compares two parsed model dicts
# ============================================================

def compare_models(current, new):
    """
    Returns a dict of all differences between two model dicts.
    """
    results = {
        "tables_added": [],
        "tables_removed": [],
        "tables_changed": {},   # model_name -> { fields_added, fields_removed, fields_changed, fk_changes }
    }

    current_names = set(current.keys())
    new_names = set(new.keys())

    results["tables_added"] = sorted(new_names - current_names)
    results["tables_removed"] = sorted(current_names - new_names)

    # Compare models that exist in both
    for model_name in sorted(current_names & new_names):
        curr = current[model_name]
        nw = new[model_name]

        curr_fields = curr["fields"]
        new_fields = nw["fields"]
        curr_fks = curr["foreign_keys"]
        new_fks = nw["foreign_keys"]

        fields_added = {k: new_fields[k] for k in new_fields if k not in curr_fields}
        fields_removed = {k: curr_fields[k] for k in curr_fields if k not in new_fields}
        fields_changed = {
            k: {"from": curr_fields[k], "to": new_fields[k]}
            for k in curr_fields
            if k in new_fields and curr_fields[k] != new_fields[k]
        }

        fk_added = {k: new_fks[k] for k in new_fks if k not in curr_fks}
        fk_removed = {k: curr_fks[k] for k in curr_fks if k not in new_fks}
        fk_changed = {
            k: {"from": curr_fks[k], "to": new_fks[k]}
            for k in curr_fks
            if k in new_fks and curr_fks[k] != new_fks[k]
        }

        if any([fields_added, fields_removed, fields_changed, fk_added, fk_removed, fk_changed]):
            results["tables_changed"][model_name] = {
                "fields_added": fields_added,
                "fields_removed": fields_removed,
                "fields_changed": fields_changed,
                "fk_added": fk_added,
                "fk_removed": fk_removed,
                "fk_changed": fk_changed,
            }

    return results


# ============================================================
# REPORT GENERATOR — formats results as markdown
# ============================================================

def generate_report(current_path, new_path, results, current_models, new_models):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    lines.append("# Django Models Schema Comparison Report")
    lines.append(f"**Generated:** {date}")
    lines.append(f"**Current models:** `{current_path}`")
    lines.append(f"**New branch models:** `{new_path}`")
    lines.append("")

    # --- Risk assessment ---
    has_removals = results["tables_removed"] or any(
        v["fields_removed"] for v in results["tables_changed"].values()
    )
    lines.append("## ⚠️ Risk Assessment")
    if has_removals:
        lines.append("**HIGH RISK** — migrations will DROP tables or columns. Data loss possible.")
    else:
        lines.append("**LOW RISK** — only additions detected. Existing data is safe.")
    lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append(f"- Tables added:    {len(results['tables_added'])}")
    lines.append(f"- Tables removed:  {len(results['tables_removed'])}")
    lines.append(f"- Tables modified: {len(results['tables_changed'])}")
    lines.append("")

    # --- Tables added ---
    if results["tables_added"]:
        lines.append("## ✅ Tables Added (safe — no data loss)")
        for t in results["tables_added"]:
            lines.append(f"### `{t}`")
            fields = new_models[t]["fields"]
            for fname, ftype in fields.items():
                lines.append(f"- `{fname}`: {ftype}")
            lines.append("")

    # --- Tables removed ---
    if results["tables_removed"]:
        lines.append("## ❌ Tables Removed (DANGER — all data in these tables will be lost)")
        for t in results["tables_removed"]:
            lines.append(f"### `{t}`")
            fields = current_models[t]["fields"]
            for fname, ftype in fields.items():
                lines.append(f"- `{fname}`: {ftype}")
            lines.append("")

    # --- Tables modified ---
    if results["tables_changed"]:
        lines.append("## 🔄 Tables Modified")
        for model_name, changes in results["tables_changed"].items():
            lines.append(f"### `{model_name}`")

            if changes["fields_added"]:
                lines.append("**Columns Added** (safe — existing rows get default value):")
                for fname, ftype in changes["fields_added"].items():
                    lines.append(f"- ✅ `{fname}`: {ftype}")

            if changes["fields_removed"]:
                lines.append("**Columns Removed** (DANGER — data in these columns will be lost):")
                for fname, ftype in changes["fields_removed"].items():
                    lines.append(f"- ❌ `{fname}`: {ftype}")

            if changes["fields_changed"]:
                lines.append("**Columns Changed:**")
                for fname, change in changes["fields_changed"].items():
                    lines.append(f"- 🔄 `{fname}`:")
                    lines.append(f"  - from: `{change['from']}`")
                    lines.append(f"  - to:   `{change['to']}`")

            if changes["fk_added"]:
                lines.append("**Foreign Keys Added:**")
                for fname, ftype in changes["fk_added"].items():
                    lines.append(f"- ✅ `{fname}`: {ftype}")

            if changes["fk_removed"]:
                lines.append("**Foreign Keys Removed:**")
                for fname, ftype in changes["fk_removed"].items():
                    lines.append(f"- ❌ `{fname}`: {ftype}")

            if changes["fk_changed"]:
                lines.append("**Foreign Keys Changed:**")
                for fname, change in changes["fk_changed"].items():
                    lines.append(f"- 🔄 `{fname}`:")
                    lines.append(f"  - from: `{change['from']}`")
                    lines.append(f"  - to:   `{change['to']}`")

            lines.append("")

    # --- Side by side table comparison ---
    lines.append("## Side by Side Table Comparison")
    all_models = sorted(set(list(current_models.keys()) + list(new_models.keys())))
    for model_name in all_models:
        lines.append(f"### `{model_name}`")
        curr_fields = current_models.get(model_name, {}).get("fields", {})
        new_fields = new_models.get(model_name, {}).get("fields", {})
        all_fields = sorted(set(list(curr_fields.keys()) + list(new_fields.keys())))

        lines.append("| Field | Current branch | New branch |")
        lines.append("|---|---|---|")
        for field in all_fields:
            curr_val = curr_fields.get(field, "—")
            new_val = new_fields.get(field, "—")
            if curr_val == "—":
                row = f"| `{field}` | — | ✅ {new_val} |"
            elif new_val == "—":
                row = f"| `{field}` | {curr_val} | ❌ removed |"
            elif curr_val != new_val:
                row = f"| `{field}` | {curr_val} | 🔄 {new_val} |"
            else:
                row = f"| `{field}` | {curr_val} | ✅ unchanged |"
            lines.append(row)
        lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python compare_models.py <current_models.py> <new_models.py> <output.md>")
        sys.exit(1)

    current_path = sys.argv[1]
    new_path = sys.argv[2]
    output_path = sys.argv[3]

    for path in [current_path, new_path]:
        if not os.path.exists(path):
            print(f"ERROR: file not found: {path}")
            sys.exit(1)

    print(f"  Parsing current models:    {current_path}")
    current_models = parse_models(current_path)
    print(f"  Parsing new branch models: {new_path}")
    new_models = parse_models(new_path)

    print(f"  Comparing...")
    results = compare_models(current_models, new_models)

    print(f"  Generating report...")
    report = generate_report(current_path, new_path, results, current_models, new_models)

    with open(output_path, "w") as f:
        f.write(report)

    print(f"  Report saved to: {output_path}")

    # Print a short terminal summary
    print("")
    print("  --- SUMMARY ---")
    if results["tables_added"]:
        print(f"  ✅ Tables added:    {', '.join(results['tables_added'])}")
    if results["tables_removed"]:
        print(f"  ❌ Tables removed:  {', '.join(results['tables_removed'])}")
    if results["tables_changed"]:
        for model, changes in results["tables_changed"].items():
            if changes["fields_added"]:
                print(f"  ✅ {model}: columns added:   {', '.join(changes['fields_added'].keys())}")
            if changes["fields_removed"]:
                print(f"  ❌ {model}: columns removed: {', '.join(changes['fields_removed'].keys())}")
            if changes["fields_changed"]:
                print(f"  🔄 {model}: columns changed: {', '.join(changes['fields_changed'].keys())}")
            if changes["fk_removed"]:
                print(f"  ❌ {model}: FK removed:      {', '.join(changes['fk_removed'].keys())}")
            if changes["fk_added"]:
                print(f"  ✅ {model}: FK added:        {', '.join(changes['fk_added'].keys())}")
    if not results["tables_added"] and not results["tables_removed"] and not results["tables_changed"]:
        print("  ✅ No schema differences found")
    print("  --- END SUMMARY ---")