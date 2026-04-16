#!/usr/bin/env python3
"""BM25 search index builder for kg wiki.
Scans all wiki pages, extracts sections, builds inverted index.
Output: wiki/.search_index.json

Usage:
  python3 build_search_index.py [wiki_root]
  Default wiki_root: ./wiki
"""
import sys, re, json, math
from pathlib import Path
from collections import defaultdict, Counter

STOP_WORDS = {"the","a","an","is","are","was","were","be","been","being",
              "have","has","had","do","does","did","will","would","shall",
              "should","may","might","can","could","and","or","but","if",
              "then","else","when","at","by","for","with","from","to","in",
              "of","on","this","that","it","its","not","no","so","as","up"}

META_FILES = {"index.md","hot.md","log.md","overview.md","graph-report.md","_index.md"}


def tokenize(text):
    """Split into tokens. Handles Korean (CJK) by character-level bigrams + Latin words."""
    tokens = []
    # Latin words
    for w in re.findall(r"[a-zA-Z0-9_-]+", text.lower()):
        if w not in STOP_WORDS and len(w) > 1:
            tokens.append(w)
    # Korean/CJK: character bigrams
    cjk = re.findall(r"[\uAC00-\uD7AF\u4E00-\u9FFF\u3040-\u30FF]+", text)
    for chunk in cjk:
        if len(chunk) >= 2:
            for i in range(len(chunk) - 1):
                tokens.append(chunk[i:i+2])
        elif len(chunk) == 1:
            tokens.append(chunk)
    return tokens


def extract_sections(text):
    """Split markdown into sections. Returns list of (heading, body) tuples."""
    sections = []
    current_heading = "(top)"
    current_body = []
    for line in text.split("\n"):
        m = re.match(r"^(#{1,3})\s+(.+)", line)
        if m:
            if current_body:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = m.group(2).strip()
            current_body = []
        else:
            current_body.append(line)
    if current_body:
        sections.append((current_heading, "\n".join(current_body)))
    return sections


def parse_frontmatter(text):
    """Extract YAML frontmatter as dict."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}, text
    try:
        import yaml
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    body = text[m.end():]
    return fm, body


def build_index(wiki_root):
    """Build BM25 inverted index from wiki pages."""
    wiki = Path(wiki_root)
    docs = {}       # doc_id -> {path, title, class, folder, sections}
    postings = defaultdict(list)  # term -> [(doc_id, section_idx, tf)]
    doc_lengths = {}

    doc_id = 0
    for md in sorted(wiki.rglob("*.md")):
        if md.name in META_FILES:
            continue
        rel = str(md.relative_to(wiki))
        if rel.startswith("."):
            continue

        text = md.read_text()
        fm, body = parse_frontmatter(text)
        title = fm.get("title", md.stem)
        instance_of = fm.get("instance_of", fm.get("type", "unknown"))
        folder = md.parent.name
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        sections = extract_sections(body)
        doc_tokens = []

        # Boost title/tags only once (at doc level), not per-section
        title_tokens = tokenize(title) * 3
        tag_tokens = []
        for t in tags:
            tag_tokens.extend(tokenize(str(t)) * 2)

        for sec_idx, (heading, sec_body) in enumerate(sections):
            tokens = tokenize(f"{heading} {sec_body}")
            # Add title/tag boost only to first section to avoid over-weighting long docs
            all_tokens = tokens + (title_tokens + tag_tokens if sec_idx == 0 else [])
            tf = Counter(all_tokens)
            for term, count in tf.items():
                postings[term].append((doc_id, sec_idx, count))
            doc_tokens.extend(all_tokens)

        docs[doc_id] = {
            "path": rel,
            "title": title,
            "class": instance_of,
            "folder": folder,
            "section_count": len(sections),
            "sections": [s[0] for s in sections],
        }
        doc_lengths[doc_id] = len(doc_tokens)
        doc_id += 1

    # BM25 parameters
    N = len(docs)
    avgdl = sum(doc_lengths.values()) / max(N, 1)
    k1, b = 1.5, 0.75

    # Compute IDF
    idf = {}
    for term, posting_list in postings.items():
        df = len(set(p[0] for p in posting_list))
        idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    return {
        "version": 1,
        "doc_count": N,
        "avg_doc_length": round(avgdl, 1),
        "bm25_params": {"k1": k1, "b": b},
        "docs": docs,
        "doc_lengths": doc_lengths,
        "idf": {k: round(v, 4) for k, v in idf.items()},
        "postings": {k: v for k, v in postings.items()},
    }


def search(index, query, top_k=10):
    """BM25 search. Returns [(doc_id, score, path, title)] sorted by score."""
    tokens = tokenize(query)
    scores = defaultdict(float)
    k1 = index["bm25_params"]["k1"]
    b = index["bm25_params"]["b"]
    avgdl = index["avg_doc_length"]

    for token in tokens:
        if token not in index["idf"]:
            continue
        token_idf = index["idf"][token]
        for doc_id, sec_idx, tf in index["postings"].get(token, []):
            doc_id_str = str(doc_id)
            dl = index["doc_lengths"].get(doc_id_str, index["doc_lengths"].get(doc_id, avgdl))
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avgdl)
            scores[doc_id] += token_idf * numerator / denominator

    results = []
    for doc_id, score in sorted(scores.items(), key=lambda x: -x[1])[:top_k]:
        doc = index["docs"].get(str(doc_id), index["docs"].get(doc_id, {}))
        results.append({
            "doc_id": doc_id,
            "score": round(score, 3),
            "path": doc.get("path", ""),
            "title": doc.get("title", ""),
            "class": doc.get("class", ""),
            "sections": doc.get("sections", []),
        })
    return results


if __name__ == "__main__":
    wiki_root = sys.argv[1] if len(sys.argv) > 1 else "wiki"
    index = build_index(wiki_root)
    out = Path(wiki_root) / ".search_index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    print(f"Indexed {index['doc_count']} docs, {len(index['idf'])} unique terms → {out}")

    # Demo search if query provided
    if len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        results = search(index, query)
        print(f"\nSearch: '{query}'")
        for r in results[:5]:
            print(f"  {r['score']:.2f} | {r['class']:12s} | {r['path']} — {r['title']}")
