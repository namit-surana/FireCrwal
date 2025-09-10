# pip install tiktoken
import json, re, time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# =========================
# 1) STATE & RULES
# =========================
EMPTY_STATE: Dict[str, Any] = {
    "certification_state": {
        "artifact_type": None,
        "name": None,
        "aliases": [],
        "issuing_body": None,
        "region": None,
        "mandatory": None,
        "validity_period_months": None,
        "overview": None,
        "full_description": None,
        "legal_reference": None,
        "domain_tags": [],
        "scope_tags": [],
        "harmonized_standards": [],
        "fee": None,
        "application_process": None,
        "official_link": None,
        "updated_at": None,
        "sources": [],
        "lead_time_days": None,
        "processing_time_days": None,
        "prerequisites": [],
        "audit_scope": [],
        "test_items": []
    }
}

SYSTEM_PROMPT_P3_PARAMETER = """
You are an expert structured data extractor for certifications.

Property Definitions:
- artifact_type (text enum, required): One of: product_certification, management_system_certification, registration, market_access_authorisation, shipment_document
- name (text): Official scheme title as published by governing body (exact official name only)
- aliases (text[]): List of common alternative names, abbreviations or legacy labels (0-5 entries)
- issuing_body (text): Full proper name of the organization that issues/governs the scheme
- region (text): Geographic scope (use: "EU/EEA", "United States", "Global", "China Mainland")
- mandatory (bool): true if legally required to place products in region; false if voluntary
- validity_period_months (number): Renewal cycle in months (e.g., 36 = 3 years; 0 = no fixed expiry)
- overview (text): 1-2 sentence plain-language summary (max 400 UTF-8 characters)
- full_description (text): 80-150 word paragraph describing purpose, scope, applicability, use cases
- legal_reference (text): Official citation (e.g., "Directive 2011/65/EU", "ISO 9001:2015")
- domain_tags (text[]): Pick 1-2 from controlled list (use snake_case)
- scope_tags (text[]): 0-10 tokens defining product families/sectors (singular nouns, snake_case)
- harmonized_standards (text[]): List specific EN/IEC/ISO test standards referenced
- fee (text): Typical cost range with currency and context (e.g., "≈ €450 per model")
- application_process (text): Brief bullet steps or URL describing how to obtain/renew (max 300 chars)
- official_link (text): Canonical URL of official scheme documentation
- updated_at (date): ISO-8601 UTC timestamp (YYYY-MM-DDThh:mm:ssZ) when record last reviewed
- sources (text[]): List of all source URLs/PDFs used to populate this record
- lead_time_days (number): Typical processing time from submission to issuance (calendar days, 0 if immediate)
- processing_time_days (number): Internal administrative processing time (business days)
- prerequisites (text[]): Required pre-conditions, prior certifications, or documentation needed
- audit_scope (text[]): Areas/processes/systems covered during audit (management systems primarily)
- test_items (text[]): Product components/materials/parameters tested (product certifications primarily)

Rules:
- Fill in only fields that can be explicitly inferred from the new content
- Do not invent or add new fields beyond the provided state
- Keep the JSON structure exactly the same as the input state
- Use null or empty arrays for fields not found in the new content
- Return **strict JSON only** with all fields present
- Summarize or clean information as needed, keeping types consistent (string, boolean, list, number, etc.)
""".strip()

# =========================
# 2) VALIDATION & MERGE
# =========================
STRING_FIELDS = {
    "artifact_type","name","issuing_body","region","overview","full_description",
    "legal_reference","fee","application_process","official_link","updated_at"
}
BOOL_FIELDS = {"mandatory"}
NUMBER_FIELDS = {"validity_period_months","lead_time_days","processing_time_days"}
LIST_STRING_FIELDS = {
    "aliases","domain_tags","scope_tags","harmonized_standards",
    "sources","prerequisites","audit_scope","test_items"
}

def _is_empty(val):
    return val in (None, "", []) or (isinstance(val, dict) and not val)

def _dedupe_str_list(lst):
    seen, out = set(), []
    for x in lst or []:
        if not isinstance(x, str):
            continue
        k = x.strip()
        if k and k not in seen:
            seen.add(k); out.append(k)
    return out

def validate_state_shape(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure exact keys and sane types; coerce where safe."""
    if not isinstance(obj, dict) or "certification_state" not in obj:
        raise ValueError("Top-level must have 'certification_state'")
    cs = obj["certification_state"]
    expected = set(EMPTY_STATE["certification_state"].keys())
    if set(cs.keys()) != expected:
        missing = expected - set(cs.keys())
        extra = set(cs.keys()) - expected
        raise ValueError(f"State keys mismatch. Missing: {missing}, Extra: {extra}")

    clean = deepcopy(obj)
    cs = clean["certification_state"]

    for k in STRING_FIELDS:
        if cs[k] is not None and not isinstance(cs[k], str):
            cs[k] = str(cs[k])

    for k in BOOL_FIELDS:
        if cs[k] is not None and not isinstance(cs[k], bool):
            sv = str(cs[k]).lower()
            if sv in ("true","false"):
                cs[k] = (sv == "true")
            else:
                raise ValueError(f"'{k}' must be boolean")

    for k in NUMBER_FIELDS:
        if cs[k] is not None and not isinstance(cs[k], (int, float)):
            s = str(cs[k]).strip()
            if re.fullmatch(r"-?\d+(\.\d+)?", s):
                cs[k] = float(s) if "." in s else int(s)
            else:
                raise ValueError(f"'{k}' must be number")

    for k in LIST_STRING_FIELDS:
        if not isinstance(cs[k], list):
            raise ValueError(f"'{k}' must be list")
        cs[k] = _dedupe_str_list(cs[k])

    return clean

def merge_cert_state(base_state: Dict[str, Any],
                     candidate_state: Dict[str, Any],
                     prefer_overwrite: bool = False,
                     page_url: Optional[str] = None) -> Dict[str, Any]:
    """Merge candidate into base. Scalars fill empties (or overwrite); lists union de-dupe; sources add URL."""
    base = deepcopy(base_state)
    b = base["certification_state"]
    c = candidate_state["certification_state"]

    for k in STRING_FIELDS | BOOL_FIELDS | NUMBER_FIELDS:
        if prefer_overwrite:
            if not _is_empty(c[k]):
                b[k] = c[k]
        else:
            if _is_empty(b[k]) and not _is_empty(c[k]):
                b[k] = c[k]

    for k in LIST_STRING_FIELDS:
        b[k] = _dedupe_str_list((b.get(k) or []) + (c.get(k) or []))

    if page_url:
        b["sources"] = _dedupe_str_list(b["sources"] + [page_url])

    return base

# =========================
# 3) TOKEN COUNTING
# =========================
import tiktoken

def _get_encoding(model: str = "gpt-4o"):
    try:
        return tiktoken.encoding_for_model(model)
    except Exception:
        return tiktoken.get_encoding("cl100k_base")

def count_text_tokens(text: str, model: str = "gpt-4o") -> int:
    return len(_get_encoding(model).encode(text or ""))

def count_messages_tokens(messages: List[Dict[str, str]], model: str = "gpt-4o") -> int:
    enc = _get_encoding(model)
    tpm, tpn = 3, 1
    total = 0
    for m in messages:
        total += tpm
        if "name" in m and m["name"]:
            total += tpn
        total += len(enc.encode(m.get("content", "") or ""))
    total += 3
    return total

def token_report_for_pages(pages: List[Dict[str, Any]],
                           system_prompt: str,
                           current_state: Dict[str, Any],
                           model: str = "gpt-4o") -> Dict[str, Any]:
    rows, total_raw, total_prompt = [], 0, 0
    for i, p in enumerate(pages, 1):
        url = p.get("url", f"page_{i}")
        page_text = (p.get("markdown") or "") + "\n\n" + (p.get("summary") or "")
        raw_tokens = count_text_tokens(page_text, model=model)
        user_prompt = (
            system_prompt.strip()
            + "\n\nCurrent State JSON (keep shape; all keys present):\n"
            + json.dumps(current_state, ensure_ascii=False)
            + "\n\nPage Content:\n"
            + page_text
            + "\n\nReturn strict JSON only (no prose), exactly the same structure as Current State JSON."
        )
        messages = [
            {"role": "system", "content": "Return strict JSON only. No explanations."},
            {"role": "user", "content": user_prompt},
        ]
        prompt_tokens = count_messages_tokens(messages, model=model)
        rows.append({"index": i, "url": url, "raw_page_tokens": raw_tokens, "prompt_tokens": prompt_tokens})
        total_raw += raw_tokens; total_prompt += prompt_tokens
    return {
        "model": model,
        "per_page": rows,
        "totals": {
            "total_raw_page_tokens": total_raw,
            "total_prompt_tokens": total_prompt,
            "avg_raw_page_tokens": total_raw / max(len(pages), 1),
            "avg_prompt_tokens": total_prompt / max(len(pages), 1),
        },
    }

# =========================
# 4) TOKEN-AWARE PROMPTING
# =========================
_BOILERPLATE_PAT = re.compile(
    r"""(?ix)
    ^\s*(Skip\ to\ main\ content.*)$|
    ^\s*(Share\ this\ page.*)$|
    ^\s*(An\ official\ website.*)$|
    ^\s*(How\ do\ you\ know\?).*$|
    ^\s*([A-Z][A-Z ]{6,}\n)$|
    ^\s*(X|Facebook|LinkedIn|E-mail).*$|
    ^\s*More\ share\ options.*$
    """, flags=re.MULTILINE
)

def clean_markdown(md: str) -> str:
    if not md:
        return ""
    md = re.sub(_BOILERPLATE_PAT, "", md)
    md = re.sub(r"^\s*!\[.*?\]\(.*?\)\s*$", "", md, flags=re.MULTILINE)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()

def signal_lines(md: str, keywords=None) -> str:
    keywords = keywords or []
    lines = md.splitlines()
    kept = []
    kw_re = re.compile("|".join([re.escape(k) for k in keywords]), re.I) if keywords else None
    for ln in lines:
        if ln.startswith(("#", "##", "###", "-", "*", "•", "1.", "2.", "3.")):
            kept.append(ln)
        elif kw_re and kw_re.search(ln):
            kept.append(ln)
    seen, out = set(), []
    for l in kept:
        k = l.strip()
        if k and k not in seen:
            seen.add(k); out.append(l)
    return "\n".join(out)

def trim_to_tokens(text: str, max_tokens: int, model="gpt-4o") -> str:
    if count_text_tokens(text, model) <= max_tokens:
        return text
    sents = re.split(r'(?<=[\.\!\?])\s+', text)
    out, enc = [], _get_encoding(model)
    for s in sents:
        if len(enc.encode("\n".join(out + [s]))) > max_tokens:
            break
        out.append(s)
    if out:
        return " ".join(out)
    toks = enc.encode(text)
    return enc.decode(toks[:max_tokens])

FIELD_KEYWORDS = {
    "artifact_type": ["certification", "registration", "market access", "shipment document", "management system"],
    "name": ["Directive", "Regulation", "standard", "scheme", "official name", "title"],
    "issuing_body": ["European Commission", "authority", "ministry", "agency"],
    "region": ["EU", "EEA", "United States", "China", "Global"],
    "mandatory": ["mandatory", "required", "voluntary", "legally required"],
    "validity_period_months": ["validity", "renewal", "expiry", "period", "months", "years"],
    "overview": ["overview", "purpose", "summary", "scope"],
    "full_description": ["scope", "applicability", "requirements", "use", "applies"],
    "legal_reference": ["Directive", "Regulation", "ISO", "EN", "IEC", "CELEX", "2011/65/EU", "32011L0065"],
    "domain_tags": ["electronics", "electrical", "EEE", "waste", "environment", "chemicals"],
    "scope_tags": ["category", "equipment", "product", "devices", "apparatus"],
    "harmonized_standards": ["EN", "IEC", "ISO", "harmonised standard"],
    "fee": ["fee", "cost", "charges"],
    "application_process": ["apply", "application", "how to obtain", "renew", "procedure", "steps"],
    "official_link": ["Official Journal", "eur-lex", "official", "consolidated version"],
    "lead_time_days": ["processing time", "lead time", "calendar days", "decision", "takes"],
    "processing_time_days": ["administrative", "business days", "processing"],
    "prerequisites": ["prerequisite", "require", "documentation", "prior certification"],
    "audit_scope": ["audit", "assessment", "management system", "scope"],
    "test_items": ["substances", "tests", "tested", "hazardous", "lead", "mercury", "cadmium", "PBB", "PBDE", "DEHP", "BBP", "DBP", "DIBP"],
    "sources": ["http", "https"],
}

def extract_snippets_for_field(md: str, field: str, max_snippets=6, window_lines=3) -> List[str]:
    kws = FIELD_KEYWORDS.get(field, [])
    if not kws:
        return []
    lines = md.splitlines()
    hits = []
    pat = re.compile("|".join([re.escape(k) for k in kws]), re.I)
    for i, ln in enumerate(lines):
        if pat.search(ln):
            start = max(0, i - window_lines)
            end = min(len(lines), i + window_lines + 1)
            snippet = "\n".join(lines[start:end]).strip()
            hits.append(snippet)
    dedup, seen = [], set()
    for h in hits:
        k = re.sub(r"\s+", " ", h)
        if k not in seen:
            seen.add(k); dedup.append(h)
        if len(dedup) >= max_snippets:
            break
    return dedup

def build_sparse_prompt(system_rules: str,
                        state: Dict[str, Any],
                        page_text: str,
                        model="gpt-4o",
                        max_total_tokens: int = 60000,
                        reserve_for_output: int = 4000):
    cleaned = clean_markdown(page_text)
    sig = signal_lines(cleaned, keywords=["Directive","Regulation","EEE","hazardous","exemption","Annex","EN","IEC","ISO","fee","apply","official"])
    cs = state["certification_state"]
    empty_fields = [k for k, v in cs.items() if (v in (None, "", []) and k != "updated_at")]

    target_schema = {"certification_state": {k: cs[k] for k in cs.keys() if k in empty_fields}}
    if "sources" not in target_schema["certification_state"]:
        target_schema["certification_state"]["sources"] = []

    per_field_blocks = []
    for f in empty_fields:
        snips = extract_snippets_for_field(sig, f, max_snippets=6)
        if snips:
            per_field_blocks.append(f"### FIELD: {f}\n" + "\n---\n".join(snips))
    evidence_block = "\n\n".join(per_field_blocks) if per_field_blocks else sig

    user_msg = (
        system_rules.strip()
        + "\n\nONLY FILL THE FIELDS PRESENT IN THIS JSON (keep exact shape/keys; others must remain untouched in your output):\n"
        + json.dumps(target_schema, ensure_ascii=False)
        + "\n\nEVIDENCE (snippets from the page; use exact facts, do not guess):\n"
        + (evidence_block or "")
        + "\n\nReturn STRICT JSON ONLY in the FULL original shape (all fields) by merging your filled values into the original state. "
          "For any field you cannot fill with certainty from the EVIDENCE, keep it null or empty array. "
          "Do not invent. No prose."
    )

    messages = [
        {"role": "system", "content": "Return strict JSON only. No explanations."},
        {"role": "user", "content": user_msg},
    ]
    budget = max_total_tokens - reserve_for_output
    used = count_messages_tokens(messages, model)
    if used > budget:
        head = system_rules.strip() + "\n\nONLY FILL THE FIELDS PRESENT IN THIS JSON (keep exact shape/keys; others must remain untouched in your output):\n" \
               + json.dumps(target_schema, ensure_ascii=False) + "\n\nEVIDENCE (trimmed):\n"
        ev = trim_to_tokens(evidence_block, max_tokens=int(budget * 0.8), model=model)
        user_msg = head + ev + "\n\nReturn STRICT JSON ONLY in the FULL original shape."
        messages = [
            {"role": "system", "content": "Return strict JSON only. No explanations."},
            {"role": "user", "content": user_msg},
        ]
        while count_messages_tokens(messages, model) > budget:
            ev = trim_to_tokens(ev, max_tokens=max(500, int(len(_get_encoding(model).encode(ev)) * 0.9)), model=model)
            messages[1]["content"] = head + ev + "\n\nReturn STRICT JSON ONLY in the FULL original shape."

    dbg = {"empty_fields": empty_fields, "prompt_tokens": count_messages_tokens(messages, model), "budget_tokens": budget}
    return messages, dbg

# =========================
# 5) ROBUST JSON CALLER
# =========================
def extract_json_or_none(text: str) -> Optional[Dict[str, Any]]:
    if not text or not text.strip():
        return None
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        try:
            return json.loads(s)
        except Exception:
            pass
    m = re.search(r"```json\s*(\{.*?\})\s*```", s, flags=re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    first, last = s.find("{"), s.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = s[first:last+1]
        try:
            return json.loads(candidate)
        except Exception:
            candidate2 = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate2)
            except Exception:
                return None
    return None

def call_llm_json(client,
                  model: str,
                  messages: List[Dict[str, str]],
                  *,
                  max_retries: int = 2,
                  response_format_json: bool = True,
                  retry_backoff_seconds: float = 0.5,
                  kwargs_support: Optional[Dict[str, Any]] = None
                  ) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    kwargs_support = kwargs_support or {}
    for attempt in range(1, max_retries + 2):
        req = dict(model=model, messages=messages, temperature=0, **kwargs_support)
        if response_format_json:
            req["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**req)
        choice = resp.choices[0]
        raw = getattr(choice.message, "content", None) or ""
        finish_reason = getattr(choice, "finish_reason", None)
        parsed = extract_json_or_none(raw)
        if parsed is not None:
            return parsed, raw, finish_reason
        if attempt <= max_retries:
            time.sleep(retry_backoff_seconds * attempt)
            messages = [
                {"role": "system", "content": "Return strict JSON only. No explanations."},
                {"role": "user", "content": "Output the JSON object only, with the exact schema previously requested. No prose, no code fences."}
            ]
            continue
        return None, raw, finish_reason

# =========================
# 6) INGESTION LOOP (TOKEN-AWARE)
# =========================
def ingest_pages_token_aware(client,
                             model: str,
                             pages: List[Dict[str, Any]],
                             initial_state: Dict[str, Any],
                             system_rules: str,
                             prefer_overwrite: bool = False,
                             model_context_tokens: int = 60000,
                             reserve_for_output: int = 4000
                             ) -> Dict[str, Any]:
    state = deepcopy(initial_state)
    for p in pages:
        page_text = (p.get("markdown") or "") + "\n\n" + (p.get("summary") or "")
        url = p.get("url")
        messages, dbg = build_sparse_prompt(
            system_rules=system_rules,
            state=state,
            page_text=page_text,
            model=model,
            max_total_tokens=model_context_tokens,
            reserve_for_output=reserve_for_output
        )
        candidate, raw, finish_reason = call_llm_json(
            client=client,
            model=model,
            messages=messages,
            max_retries=2,
            response_format_json=True,
            kwargs_support={}
        )
        if not candidate:
            print(f"[SKIP] {url or 'page'} invalid JSON/state (finish_reason={finish_reason}): {(raw or '')[:160]}...")
            continue
        try:
            candidate = validate_state_shape(candidate)
        except Exception as e:
            print(f"[SKIP] {url or 'page'} schema fail: {e}")
            continue
        state = merge_cert_state(state, candidate, prefer_overwrite=prefer_overwrite, page_url=url)

    state = deepcopy(state)
    state["certification_state"]["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return state

# =========================
# 7) EXAMPLE USAGE
# =========================
if __name__ == "__main__":
    # Example pages list (replace with your real scraped data)
    with open ('/Users/kerr/Mangrove AI/FireCrwal/relevance/data/EU_Certs/Data/eu_complicance_search1_processed.json', "r", encoding='utf-8') as f:
        input = json.load(f)

    # # 1) (Optional) token report
    # tr = token_report_for_pages(
    #     pages=pages,
    #     system_prompt=SYSTEM_PROMPT_P3_PARAMETER,
    #     current_state=EMPTY_STATE,
    #     model="gpt-4o"
    # )
    # print(json.dumps(tr["totals"], indent=2))

    #2) Run ingestion (requires an OpenAI-style `client` object)
    from openai import OpenAI
    client = OpenAI()
    final_state = ingest_pages_token_aware(
        client=client,
        model="gpt-4o",
        pages=input,
        initial_state=EMPTY_STATE,
        system_rules=SYSTEM_PROMPT_P3_PARAMETER,
        prefer_overwrite=False,
        model_context_tokens=60000,
        reserve_for_output=4000
    )
    print(json.dumps(final_state, indent=2, ensure_ascii=False))
