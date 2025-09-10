"""
System prompts for certification ingestion and processing.
"""

import json

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
- other_relevant_info: Additional context or notes relevant to the certification

Rules:
- Fill in only fields that can be explicitly inferred from the new content
- Do not invent or add new fields beyond the provided state
- Keep the JSON structure exactly the same as the input state
- Use null or empty arrays for fields not found in the new content
- Return **strict JSON only** with all fields present
- Summarize or clean information as needed, keeping types consistent (string, boolean, list, number, etc.)
"""


def build_webpage_ingestion_prompt(current_state, webpage_data):
    """Build prompt for ingesting webpage results for fill-in-the-blank functionality"""
    return f"""
Current state:
{json.dumps(current_state, indent=2, ensure_ascii=False)}

Webpage Data:
{webpage_data}

Task:
- Update the current state with information from the webpage content using the property definitions in the SYSTEM_PROMPT
- Fill in only fields that can be explicitly inferred from the content
- Leave other fields as they are (null, empty, or [])
- Return JSON matching exactly the state structure above
- Do NOT invent fields or change the structure; only fill in relevant values
- You should not restrict character limits - there is no rule on how many words should be in each field; when you find details relevant to a specific field, include ALL relevant information found in the content

Return only the JSON object, no additional text.
"""


# Default certification state template
CERTIFICATION_STATE = {
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
    "test_items": [],
    "other_relevant_info": None
}


def get_certification_state():
    """Return a copy of the default certification state"""
    return CERTIFICATION_STATE.copy()