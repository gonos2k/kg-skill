#!/usr/bin/env python3
"""kg schema validator. Checks page frontmatter+body against core.yaml.
Also enforces relation domain/range and contract consistency.
Uses --schema-dir <path> to point at a per-wiki pin; otherwise falls back
to the global default schema (the directory this script lives in)."""
import sys, re, yaml, argparse
from pathlib import Path

GLOBAL_SCHEMA_DIR = Path(__file__).resolve().parent.parent


def resolve_schema_dir(args=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--schema-dir", type=Path, default=None)
    known, remaining = parser.parse_known_args(args)
    if known.schema_dir and known.schema_dir.exists():
        return known.schema_dir, remaining
    return GLOBAL_SCHEMA_DIR, remaining


def load(schema_dir):
    core = yaml.safe_load((schema_dir / "core.yaml").read_text())
    rels = yaml.safe_load((schema_dir / "relations.yaml").read_text())
    return core, rels


def parse_page(path):
    txt = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)", txt, re.DOTALL)
    if not m:
        return None, txt
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def sections(body):
    return set(re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE))


def _type_allows(declared, actual):
    if declared in ("any", None):
        return True
    if isinstance(declared, list):
        return actual in declared
    return declared == actual


def _resolve_target_class(target, wiki_root, core):
    slug = str(target).strip("[]").split("|")[0].strip()
    for folder in ("entities", "concepts", "procedures", "experiences",
                    "heuristics", "decisions", "sources", "queries"):
        cand = wiki_root / folder / f"{slug}.md"
        if not cand.exists():
            continue
        fm, _ = parse_page(cand)
        if fm and fm.get("instance_of"):
            return fm["instance_of"]
        legacy = core.get("legacy_mode", {}).get(folder)
        if legacy:
            return legacy["implicit_instance_of"]
    return None


META_PAGES = {"index.md", "hot.md", "log.md", "overview.md", "graph-report.md", "_index.md"}
OLD_TYPE_MAP = {
    "entity": "Artifact", "concept": "Concept", "source": "Source",
    "query": "Concept", "overview": "Concept",
}


def check_page(path, core, rels, wiki_root=None):
    if path.name in META_PAGES:
        return []  # meta pages are not ontology instances — skip validation
    fm, body = parse_page(path)
    errs = []
    if wiki_root is None:
        wiki_root = path.parent.parent

    # Legacy resolution: 3 cases
    # 1. No frontmatter at all → folder-based implicit class
    # 2. Frontmatter with old `type:` but no `instance_of` → map type to class
    # 3. Frontmatter with `instance_of` → use directly
    if fm is None:
        folder = path.parent.name
        legacy = core.get("legacy_mode", {}).get(folder)
        if not legacy:
            errs.append(f"{path}: no frontmatter and no legacy rule for folder '{folder}'")
            return errs
        cls_name = legacy["implicit_instance_of"]
        print(f"{path}: legacy (schema_origin=legacy, implicit instance_of={cls_name})",
              file=sys.stderr)
    elif fm.get("instance_of"):
        cls_name = fm["instance_of"]
    else:
        # Has frontmatter but no instance_of — try old `type:` field
        old_type = fm.get("type", "")
        folder = path.parent.name
        if old_type in OLD_TYPE_MAP:
            cls_name = OLD_TYPE_MAP[old_type]
            print(f"{path}: legacy type='{old_type}' → {cls_name} (upgrade recommended)",
                  file=sys.stderr)
        else:
            legacy = core.get("legacy_mode", {}).get(folder)
            if legacy:
                cls_name = legacy["implicit_instance_of"]
                print(f"{path}: legacy folder '{folder}' → {cls_name}", file=sys.stderr)
            else:
                errs.append(f"{path}: no instance_of and no legacy mapping for type='{old_type}' folder='{folder}'")
                return errs

    cls = core["classes"].get(cls_name)
    if not cls:
        errs.append(f"{path}: unknown instance_of '{cls_name}'")
        return errs

    # Legacy = no frontmatter, or has frontmatter but no instance_of
    # Transitional = has instance_of but still carries old `type:` field (reclassified, body not yet restructured)
    is_legacy = fm is None or (fm is not None and not fm.get("instance_of"))
    is_transitional = fm is not None and fm.get("instance_of") and fm.get("type") in OLD_TYPE_MAP

    if fm is not None:
        if is_legacy:
            # Legacy pages: warn about missing fields, don't error
            if fm.get("page_kind") and fm.get("page_kind") not in cls["page_kinds"]:
                print(f"{path}: legacy page_kind '{fm.get('page_kind')}' not in {cls['page_kinds']}",
                      file=sys.stderr)
            for f in cls["required_frontmatter"]:
                if f not in fm:
                    print(f"{path}: legacy page missing frontmatter '{f}' (upgrade recommended)",
                          file=sys.stderr)
        elif is_transitional:
            # Transitional pages (reclassified, instance_of set but old type: remains)
            if fm.get("page_kind") and fm.get("page_kind") not in cls["page_kinds"]:
                print(f"{path}: transitional page_kind '{fm.get('page_kind')}' not in {cls['page_kinds']}",
                      file=sys.stderr)
            for f in cls["required_frontmatter"]:
                if f not in fm:
                    print(f"{path}: transitional page missing frontmatter '{f}' (upgrade recommended)",
                          file=sys.stderr)
        else:
            # Full v1 pages: enforce strictly
            if fm.get("page_kind") not in cls["page_kinds"]:
                errs.append(f"{path}: page_kind '{fm.get('page_kind')}' "
                            f"not in allowed {cls['page_kinds']} for {cls_name}")
            for f in cls["required_frontmatter"]:
                if f not in fm:
                    errs.append(f"{path}: missing frontmatter '{f}'")
        # Enum checks apply to all pages that have the field
        if "epistemic_status" in fm:
            if fm["epistemic_status"] not in core["epistemic_states"]:
                errs.append(f"{path}: unknown epistemic_status '{fm['epistemic_status']}'")
        if "confidence" in fm:
            if fm["confidence"] not in core.get("confidence_levels", []):
                errs.append(f"{path}: unknown confidence '{fm['confidence']}'")


    for s in cls["required_body_sections"]:
        if s not in sections(body):
            if is_legacy or is_transitional:
                print(f"{path}: {'legacy' if is_legacy else 'transitional'} page missing body section '{s}' (restructure recommended)",
                      file=sys.stderr)
            else:
                errs.append(f"{path}: missing body section '{s}'")

    valid_preds = {p["name"]: p for grp in rels["predicates"].values() for p in grp}
    for rel in (fm or {}).get("relations", []) or []:
        pred = rel.get("predicate")
        if pred not in valid_preds:
            errs.append(f"{path}: unknown predicate '{pred}'")
            continue
        dom = valid_preds[pred].get("domain")
        rng = valid_preds[pred].get("range")
        if not _type_allows(dom, cls_name):
            errs.append(f"{path}: predicate '{pred}' domain mismatch "
                        f"(expected {dom}, got {cls_name})")
        target_cls = _resolve_target_class(rel.get("target", ""), wiki_root, core)
        if target_cls is None:
            print(f"{path}: predicate '{pred}' target '{rel.get('target')}' unresolved",
                  file=sys.stderr)
            continue
        if not _type_allows(rng, target_cls):
            errs.append(f"{path}: predicate '{pred}' range mismatch "
                        f"(expected {rng}, target is {target_cls})")
    return errs


def check_contract(core, schema_dir):
    tpl_dir = schema_dir.parent / "templates"
    if not tpl_dir.exists():
        tpl_dir = GLOBAL_SCHEMA_DIR.parent / "templates"
    errs = []
    for name, cls in core["classes"].items():
        tpl = tpl_dir / f"{name.lower()}.md"
        if not tpl.exists():
            errs.append(f"contract: template missing for {name}")
            continue
        fm, body = parse_page(tpl)
        if fm is None:
            errs.append(f"contract: {tpl} has no frontmatter")
            continue
        for f in cls["required_frontmatter"]:
            if f not in fm:
                errs.append(f"contract: {tpl} missing required frontmatter '{f}'")
        for s in cls["required_body_sections"]:
            if s not in sections(body):
                errs.append(f"contract: {tpl} missing required section '{s}'")
        if fm.get("page_kind") not in cls["page_kinds"]:
            errs.append(f"contract: {tpl} page_kind '{fm.get('page_kind')}' "
                        f"not in {cls['page_kinds']}")
        if "epistemic_status" in fm and fm["epistemic_status"] not in core["epistemic_states"]:
            errs.append(f"contract: {tpl} has invalid epistemic_status "
                        f"'{fm['epistemic_status']}'")
        if "confidence" in fm and fm["confidence"] not in core.get("confidence_levels", []):
            errs.append(f"contract: {tpl} has invalid confidence '{fm['confidence']}'")
    return errs


def schema_fingerprint(schema_dir):
    """Hash all schema+template files. If any change, entire cache is stale."""
    import hashlib, json as _json
    parts = []
    for pattern in ["*.yaml"]:
        for f in sorted(schema_dir.glob(pattern)):
            parts.append(hashlib.sha256(f.read_bytes()).hexdigest())
    for f in sorted((schema_dir / "migrations").glob("*.yaml")):
        parts.append(hashlib.sha256(f.read_bytes()).hexdigest())
    tpl_dir = schema_dir.parent / "templates"
    if not tpl_dir.exists():
        tpl_dir = GLOBAL_SCHEMA_DIR.parent / "templates"
    if tpl_dir.exists():
        for f in sorted(tpl_dir.glob("*.md")):
            parts.append(hashlib.sha256(f.read_bytes()).hexdigest())
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def build_receipt(schema_dir, wiki_root, page_paths, core, rels,
                   proposal_path=None):
    """Run all receipt sensors and return a structured receipt dict."""
    import collections, datetime, hashlib as _hl

    receipt = {
        "date": datetime.date.today().isoformat(),
        "schema_version": core.get("schema_version", "?"),
        "checks": {},
        "gate_result": "PENDING",
    }

    # --- 1. schema_diff: compare proposal target_version vs current ---
    if proposal_path and Path(proposal_path).exists():
        pfm = yaml.safe_load(Path(proposal_path).read_text()) or {}
        tv = pfm.get("target_version")
        cv = core.get("schema_version", 1)
        if tv is not None and tv != cv + 1:
            receipt["checks"]["schema_diff"] = {
                "status": "FAIL",
                "detail": f"target_version {tv} != current {cv} + 1",
            }
        else:
            receipt["checks"]["schema_diff"] = {
                "status": "PASS",
                "detail": f"current v{cv} → v{tv or cv+1}",
            }
    else:
        receipt["checks"]["schema_diff"] = {
            "status": "SKIP", "detail": "no proposal path given",
        }

    # --- 2. template_contract ---
    contract_errs = check_contract(core, schema_dir)
    receipt["checks"]["template_contract"] = {
        "status": "PASS" if not contract_errs else "FAIL",
        "detail": f"{len(contract_errs)} errors" if contract_errs else "all templates valid",
        "errors": contract_errs[:10] if contract_errs else [],
    }

    # --- 3. frontmatter_valid: run page validation ---
    page_errs = []
    page_warns = 0
    for p in page_paths:
        path = Path(p)
        if path.name in META_PAGES:
            continue
        pe = check_page(path, core, rels, wiki_root)
        page_errs.extend(pe)

    receipt["checks"]["frontmatter_valid"] = {
        "status": "PASS" if not page_errs else "FAIL",
        "detail": f"{len(page_errs)} errors across {len(page_paths)} pages",
        "errors": page_errs[:20] if page_errs else [],
    }

    # --- 4. legacy_compat: count tiers ---
    tiers = collections.Counter()
    for p in page_paths:
        path = Path(p)
        if path.name in META_PAGES:
            continue
        fm, _ = parse_page(path)
        if fm is None:
            tiers["legacy"] += 1
        elif fm.get("instance_of") and fm.get("type") in OLD_TYPE_MAP:
            tiers["transitional"] += 1
        elif fm.get("instance_of"):
            tiers["full_v1"] += 1
        else:
            tiers["legacy"] += 1
    total = sum(tiers.values())
    receipt["checks"]["legacy_compat"] = {
        "status": "PASS",
        "detail": f"{tiers['legacy']} legacy + {tiers['transitional']} transitional unaffected",
        "tiers": dict(tiers),
        "convergence_ratio": round(tiers["full_v1"] / max(total, 1), 3),
    }

    # --- 5. evidence_pages: verify cited evidence exists ---
    if proposal_path and Path(proposal_path).exists():
        pfm = yaml.safe_load(Path(proposal_path).read_text()) or {}
        evidence = pfm.get("evidence", [])
        missing = []
        for e in evidence:
            slug = str(e).strip("[]").split("|")[0].strip()
            found = False
            for folder in ("entities", "concepts", "procedures", "experiences",
                           "heuristics", "decisions", "sources", "queries"):
                if wiki_root and (wiki_root / folder / f"{slug}.md").exists():
                    found = True
                    break
            if not found:
                missing.append(slug)
        receipt["checks"]["evidence_pages"] = {
            "status": "PASS" if not missing else "FAIL",
            "detail": f"{len(evidence)} cited, {len(missing)} missing",
            "missing": missing[:10] if missing else [],
        }
    else:
        receipt["checks"]["evidence_pages"] = {
            "status": "SKIP", "detail": "no proposal path given",
        }

    # --- 6. predicate_utilization ---
    valid_preds = {p["name"] for grp in rels["predicates"].values() for p in grp}
    used_preds = set()
    for p in page_paths:
        path = Path(p)
        if path.name in META_PAGES:
            continue
        fm, _ = parse_page(path)
        for rel in (fm or {}).get("relations", []) or []:
            used_preds.add(rel.get("predicate"))
    unused = valid_preds - used_preds
    receipt["checks"]["predicate_utilization"] = {
        "status": "PASS" if len(unused) <= len(valid_preds) * 0.5 else "ADVISORY",
        "detail": f"{len(used_preds)}/{len(valid_preds)} predicates in use",
        "unused": sorted(unused),
    }

    # --- Gate decision: all Required checks must PASS or SKIP ---
    required = ["schema_diff", "template_contract", "frontmatter_valid",
                 "legacy_compat", "evidence_pages"]
    failures = [k for k in required
                if receipt["checks"].get(k, {}).get("status") == "FAIL"]
    receipt["gate_result"] = "FAIL" if failures else "PASS"
    if failures:
        receipt["gate_failures"] = failures

    return receipt


if __name__ == "__main__":
    import hashlib, json as _json

    schema_dir, remaining = resolve_schema_dir()
    core, rels = load(schema_dir)
    errs = check_contract(core, schema_dir)

    # Parse flags
    use_cache = "--cache" in remaining
    use_summary = "--summary" in remaining
    use_receipt = "--receipt" in remaining
    remaining = [r for r in remaining if r not in ("--cache", "--summary", "--receipt")]
    wiki_root = None
    proposal_path = None
    i = 0
    while i < len(remaining):
        if remaining[i] == "--wiki-root" and i + 1 < len(remaining):
            wiki_root = Path(remaining[i + 1])
            remaining = remaining[:i] + remaining[i+2:]
            continue
        if remaining[i] == "--proposal" and i + 1 < len(remaining):
            proposal_path = remaining[i + 1]
            remaining = remaining[:i] + remaining[i+2:]
            continue
        i += 1

    # Receipt mode: structured JSON output for schema approve
    if use_receipt:
        page_paths = [p for p in remaining if not p.startswith("-")]
        receipt = build_receipt(schema_dir, wiki_root, page_paths, core, rels,
                                proposal_path)
        print(_json.dumps(receipt, indent=2, ensure_ascii=False))
        sys.exit(0 if receipt["gate_result"] == "PASS" else 1)

    cache = {}
    fp = None
    cache_file = (wiki_root or Path(".")) / ".validate_cache.json"
    if use_cache:
        fp = schema_fingerprint(schema_dir)
        if cache_file.exists():
            cache = _json.loads(cache_file.read_text())
            if cache.get("_schema_fingerprint") != fp:
                cache = {}  # schema changed, invalidate all

    for p in remaining:
        if p.startswith("-"):
            continue
        path = Path(p)
        if use_cache and fp:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            cache_key = str(path.resolve())
            if cache.get(cache_key) == h:
                continue
            page_errs = check_page(path, core, rels, wiki_root)
            errs.extend(page_errs)
            if not page_errs:
                cache[cache_key] = h
        else:
            errs.extend(check_page(Path(p), core, rels, wiki_root))

    if use_cache and fp:
        cache["_schema_fingerprint"] = fp
        cache_file.write_text(_json.dumps(cache, indent=2))

    if use_summary:
        import collections
        tiers = collections.Counter()
        for p in remaining:
            if p.startswith("-"): continue
            path = Path(p)
            if path.name in META_PAGES: continue
            fm, _ = parse_page(path)
            if fm is None:
                tiers["legacy"] += 1
            elif fm.get("instance_of") and fm.get("type") in OLD_TYPE_MAP:
                tiers["transitional"] += 1
            elif fm.get("instance_of"):
                tiers["full_v1"] += 1
            else:
                tiers["legacy"] += 1
        total = sum(tiers.values())
        print(_json.dumps({
            "total_pages": total,
            "full_v1": tiers["full_v1"],
            "transitional": tiers["transitional"],
            "legacy": tiers["legacy"],
            "convergence_ratio": round(tiers["full_v1"] / max(total, 1), 3),
            "errors": len(errs),
        }, indent=2))
        sys.exit(0)

    for e in errs:
        print(e)
    sys.exit(1 if errs else 0)
