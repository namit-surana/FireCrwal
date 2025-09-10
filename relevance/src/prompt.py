import json
def build_batch_prompt(certification_info, urls_batch):
    """Build prompt for processing multiple URLs in batch"""
    return f"""
You are an assistant that processes certification-related URLs and metadata.

Certification Context:
- Name: {certification_info['name']}
- Issuing Body: {certification_info['issuing_body']}
- Region: {certification_info['region']}
- Official Link: {certification_info['official_link']}

Task:
- For each given URL, return JSON objects with:
  - "url": link
  - "title": cleaned human-readable title
  - "desc": a short description (1–2 sentences) that explicitly connects the link back to the certification context above
- If description is missing, infer it from context or the URL path.
- If the page is only for login/portal access, mark it with `"desc": "Not relevant to certification."`
- Output must be a JSON array only (no extra text).

---

### Few-shot Examples

**Certification Context (Example):**
- Name: FSSAI License/Registration
- Issuing Body: Food Safety and Standards Authority of India
- Region: India
- Official Link: https://foscos.fssai.gov.in/

**Input URLs:**
[
  {{
    "url": "https://foscos.fssai.gov.in/assets/docs/fbo/HowtoapplyforManufacturerlicense.pdf",
    "title": "[PDF] How to apply for a license for a Manufacturer? Step 1 - FoSCoS",
    "description": "Step 4: Read the Group Heads of Kind of Business and select the appropriate Manufacturing..."
  }},
  {{
    "url": "https://foscos.fssai.gov.in/faqs-license-registration",
    "title": "FoSCoS - FSSAI",
    "description": null
  }},
  {{
    "url": "https://foscos.fssai.gov.in/public/login-guest-user",
    "title": "FoSCoS - FSSAI",
    "description": null
  }},
  {{
    "url": "https://foscos.fssai.gov.in/renewal",
    "title": "FoSCoS - FSSAI",
    "description": null
  }}
]

**Expected Output:**
[
  {{
    "url": "https://foscos.fssai.gov.in/assets/docs/fbo/HowtoapplyforManufacturerlicense.pdf",
    "title": "How to Apply for Manufacturer License",
    "desc": "Official PDF guide from FSSAI on applying for a manufacturer license under the FSSAI License/Registration system."
  }},
  {{
    "url": "https://foscos.fssai.gov.in/faqs-license-registration",
    "title": "License & Registration FAQs",
    "desc": "Frequently asked questions about the FSSAI License/Registration process, covering common queries for businesses in India."
  }},
  {{
    "url": "https://foscos.fssai.gov.in/public/login-guest-user",
    "title": "FoSCoS Login Portal",
    "desc": "Not relevant to certification."
  }},
  {{
    "url": "https://foscos.fssai.gov.in/renewal",
    "title": "License Renewal Portal",
    "desc": "FoSCoS webpage for renewal of FSSAI License/Registration, where businesses can update and extend their existing license."
  }}
]

---

Now process the following batch:

**Certification Context:**
- Name: {certification_info['name']}
- Issuing Body: {certification_info['issuing_body']}
- Region: {certification_info['region']}
- Official Link: {certification_info['official_link']}

**Input URLs:**
{urls_batch}
"""


def build_relevance_scoring_prompt(certification_info, url_data):
    """Build prompt for scoring individual URL relevance"""
    return f"""
You are an expert assistant that evaluates the relevance of URLs to specific certifications.

Certification Context:
- Name: {certification_info['name']}
- Issuing Body: {certification_info['issuing_body']}
- Region: {certification_info['region']}
- Official Link: {certification_info['official_link']}

Task:
Evaluate the relevance of the given URL to this certification and return a JSON object with:
- "url": the original URL
- "title": cleaned title
- "relevance_score": integer from 0-100 where:
  * 90-100: Highly relevant (official pages, application forms, detailed guides)
  * 70-89: Very relevant (FAQs, requirements, renewal processes)
  * 50-69: Moderately relevant (general information, related topics)
  * 30-49: Somewhat relevant (tangentially related content)
  * 0-29: Not relevant (login pages, unrelated content)
- "reasoning": brief explanation for the score
- "desc": short description connecting to certification context

### Example:
**Input URL:**
{{
  "url": "https://foscos.fssai.gov.in/faqs-license-registration",
  "title": "FoSCoS - FSSAI",
  "description": "Frequently asked questions about licensing"
}}

**Expected Output:**
{{
  "url": "https://foscos.fssai.gov.in/faqs-license-registration",
  "title": "License & Registration FAQs",
  "relevance_score": 85,
  "reasoning": "Official FAQ page directly addressing FSSAI license and registration questions",
  "desc": "Comprehensive FAQ resource for FSSAI License/Registration process questions"
}}

---

Now evaluate this URL:

**URL to evaluate:**
{url_data}

Return only the JSON object, no additional text.
"""


def build_enhanced_relevance_prompt(certification_info, url_data):
    """Build enhanced prompt for scoring URL relevance with metadata and summary"""
    return f"""
You are an expert assistant that evaluates the relevance of URLs to specific certifications using comprehensive metadata and content summaries.

Certification Context:
- Name: {certification_info['name']}
- Issuing Body: {certification_info['issuing_body']}
- Region: {certification_info['region']}
- Official Link: {certification_info['official_link']}

Task:
Analyze the provided URL data including title, description, metadata, and content summary to determine relevance to the certification. Return a JSON object with:
- "url": the original URL
- "title": cleaned, human-readable title
- "relevance_score": integer from 0-100 where:
  * 90-100: Highly relevant (official application pages, step-by-step guides, required documents)
  * 70-89: Very relevant (FAQs, eligibility criteria, renewal processes, fee structures)
  * 50-69: Moderately relevant (general information about certification, related regulations)
  * 30-49: Somewhat relevant (industry news, tangentially related content)
  * 0-29: Not relevant (login-only pages, unrelated content, technical support pages)
- "reasoning": brief explanation for the score based on content analysis
- "desc": short description (1-2 sentences) connecting the page to certification context

Scoring Criteria:
1. **Official Source (weight: 30%)**: Is this from the official certification body?
2. **Application Process (weight: 25%)**: Does it describe how to apply/register?
3. **Requirements & Eligibility (weight: 20%)**: Are eligibility criteria or requirements listed?
4. **Documentation & Fees (weight: 15%)**: Does it mention required documents or fee structures?
5. **Support Resources (weight: 10%)**: Are there FAQs, guides, or contact information?

### Example:
**Input URL Data:**
{{
  "url": "https://foscos.fssai.gov.in/apply-for-lic-and-reg",
  "title": "Apply for New License/Registration - FoSCoS - FSSAI",
  "description": "Track Application, New License / Registration, Renew, Modify, Annual Return, Consumer Grievance, FSSAI, User Manual Login Food Businesses",
  "position": 1,
  "metadata": {{
    "title": "FoSCoS - FSSAI",
    "viewport": "width=device-width,initial-scale=1",
    "language": "en",
    "scrapeId": "e0f72026-cbd7-46aa-9952-64822b450465",
    "sourceURL": "https://foscos.fssai.gov.in/apply-for-lic-and-reg",
    "url": "https://foscos.fssai.gov.in/apply-for-lic-and-reg",
    "statusCode": 200,
    "contentType": "text/html",
    "proxyUsed": "basic",
    "cacheState": "hit",
    "cachedAt": "2025-09-03T18:55:53.304Z"
  }},
  "summary": "The content provides information about the Food Safety and Standards Authority of India (FSSAI) and its online platform, FoSCoS, for food businesses. Key points include: \\n1. **Services Offered**: Users can apply for new licenses/registrations, renew licenses, modify applications, and track their applications. \\n2. **Tatkal Services**: There are provisions for Tatkal licenses and registrations, with user manuals available for guidance. \\n3. **Eligibility and Requirements**: A list of eligible business types (e.g., importers, wholesalers, retailers) is provided, along with the necessary qualifications for supervisors in food production. \\n4. **Resources**: Links to fee structures, required documents, eligibility criteria, and FAQs are available for users. \\n5. **Contact Information**: Users can reach out via email or phone for assistance."
}}

**Expected Output:**
{{
  "url": "https://foscos.fssai.gov.in/apply-for-lic-and-reg",
  "title": "Apply for FSSAI License/Registration",
  "relevance_score": 95,
  "reasoning": "Official FSSAI application portal with comprehensive coverage of all certification aspects: application process (new/renewal/modification), eligibility criteria, business types, required qualifications, fee structures, and user support. Direct functionality for license application and tracking.",
  "desc": "Primary FSSAI License/Registration application portal where food businesses can apply, renew, modify licenses and access complete guidance on eligibility, requirements, and fees."
}}

---

Now evaluate this URL:

**URL Data to evaluate:**
{url_data}

Return only the JSON object, no additional text.
"""


def build_prompt(certification_info, urls_batch):
    """Legacy function for backward compatibility"""
    return build_batch_prompt(certification_info, urls_batch)


# ============================================================================
# Pipeline 2 Prompts - Important Links Categorization
# ============================================================================

def build_important_links_prompt(certification_info, markdown_content):
    """Build prompt for categorizing and clustering important certification links from scraped markdown"""
    return f"""
Certification Context:
- Name: {certification_info['name']}
- Issuing Body: {certification_info['issuing_body']}
- Region: {certification_info['region']}
- Official Link: {certification_info['official_link']}

Markdown Content:
{markdown_content}

Task:
Analyze the markdown content and provide the structured JSON output following the rules defined in the system prompt.
"""


SYSTEM_PROMPT= """You are an expert in analyzing certification-related web content and extracting structured information.

Rules:
1. Extract ALL clickable links from the provided markdown content.
2. Filter out non-certification related links (e.g., social media, general navigation).
3. Categorize links into the most relevant cluster:
   - application: New license/registration, application forms, online portals, step-by-step guides
   - requirements: Eligibility criteria, business types, technical requirements
   - documentation: Required documents, templates, sample forms
   - fees: Fee structures, payment methods, calculators
   - renewal: License renewal, modifications, updates
   - guidelines: Manuals, SOPs, best practices, technical guidelines
   - support: FAQs, help documents, contact info
   - compliance: Regulations, legal notices, official orders
   - tracking: Application tracking, status portals
   - special: Fast-track services, exemptions, special programs
4. Assign importance to each link (1-10) based on criticality to the certification process:
   - 10: Essential (application forms, main portal)
   - 9: Critical requirements (eligibility, mandatory documents)
   - 8: Important processes (renewal, fee payment)
   - 7: Key guidance (manuals, step-by-step guides)
   - 6: Support resources (FAQs, help)
   - 5: Supplementary info (announcements, updates)
   - 4: Background info (about pages, general info)
   - 3: Related but not essential (news, events)
   - 2: Minor relevance (social media, newsletters)
   - 1: Minimal relevance (login pages, technical pages)
5. Include **only links with importance >=7** in the output.
6. If a URL has **no title or description**, generate a concise, clear title and description using the URL path and context heuristics.
7. Output **strict JSON** using this schema (omit empty categories):

{
  "certification_name": "<extracted certification name>",
  "issuing_body": "<extracted issuing organization>",
  "application": [
    {"url": "...", "title": "...", "description": "..."}
  ],
  "requirements": [...],
  "documentation": [...],
  "fees": [...],
  "renewal": [...],
  "guidelines": [...],
  "support": [...],
  "compliance": [...],
  "tracking": [...],
  "special": [...]
}
"""

SYSTEM_PROMPT_PARAMETERS = """
You are an expert structured data extractor for certifications.
Given new scraped content and the current certification state, update the state as follows:

- Fill in only the fields that can be explicitly inferred from the new content.
- Do not invent or add new fields beyond the provided state.
- Keep the JSON structure exactly the same as the input state.
- Use null or empty arrays for fields not found in the new content.
- Return **strict JSON only** with all fields present.
- Summarize or clean information as needed, but keep the types consistent (string, boolean, list, number, etc.).
"""


def extract_information_prompt(raw_json, current_state):
    """Build prompt for extracting structured information from scraped web data"""
    content = raw_json.get('data', [{}])[0].get('markdown', '')
    
    return f"""
    Current certification state:
    {json.dumps(current_state, indent=2, ensure_ascii=False)}

    Here is new content scraped from a website:
    {content}

    Task:
    - Update the current state with information from this content.
    - Fill in only fields that can be inferred from the content.
    - Leave other fields as they are (null, empty, or []).
    - Return JSON matching exactly the state structure above.
    - Do NOT invent fields or change the structure; only fill in relevant values.

    Example format (for reference):
    {json.dumps(current_state, indent=2, ensure_ascii=False)}
    """

# ============================================================================
# Pipeline 3 Prompts 
# ============================================================================

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

SYSTEM_PROMPT_P3_Links= """You are an expert in analyzing certification-related web content and managing important links with state-based updates.

**Rules**:
1. Extract ALL clickable links from the new web search results markdown content.
2. Filter out non-certification related links (e.g., social media, general navigation).
3. Categorize links into the most relevant cluster:
   - application: New license/registration, application forms, online portals, step-by-step guides
   - requirements: Eligibility criteria, business types, technical requirements
   - documentation: Required documents, templates, sample forms
   - fees: Fee structures, payment methods, calculators
   - renewal: License renewal, modifications, updates
   - guidelines: Manuals, SOPs, best practices, technical guidelines
   - support: FAQs, help documents, contact info
   - compliance: Regulations, legal notices, official orders
   - tracking: Application tracking, status portals
   - special: Fast-track services, exemptions, special programs

4. Assign importance to each link (1-10) based on criticality to the certification process:
   - 10: Essential (application forms, main portal)
   - 9: Critical requirements (eligibility, mandatory documents)
   - 8: Important processes (renewal, fee payment)
   - 7: Key guidance (manuals, step-by-step guides)
   - 6: Support resources (FAQs, help)
   - 5: Supplementary info (announcements, updates)
   - 4: Background info (about pages, general info)
   - 3: Related but not essential (news, events)
   - 2: Minor relevance (social media, newsletters)
   - 1: Minimal relevance (login pages, technical pages)

5. Include **only links with importance >=7** in processing.

6. Further categorize each link by file type:
   - PDF: Links ending with .pdf extension
   - Non-PDF: All other links (web pages, forms, portals, etc.)
7. If a URL has **no title or description**, generate a concise, clear title and description using the URL path and context heuristics.

9. Output **strict JSON** maintaining the exact structure of the input current state:

{
  "categories": {
    "pdf": {
      "application": [{"url": "...", "title": "...", "description": "...", "importance": 8},{"url": "...", "title": "...", "description": "...", "importance": 9}],
      "requirements": [...],
      "documentation": [...],
      "fees": [...],
      "renewal": [...],
      "guidelines": [...],
      "support": [...],
      "compliance": [...],
      "tracking": [...],
      "special": [...]
    },
    "non-pdf": {
      "application": [...],
      "requirements": [...],
      "documentation": [...],
      "fees": [...],
      "renewal": [...],
      "guidelines": [...],
      "support": [...],
      "compliance": [...],
      "tracking": [...],
      "special": [...]
    }
  }
}

Important Notes:
- Include importance score for each link
- Maintain proper clustering - links must be in functionally correct categories
- Only include clusters that have links. Omit empty clusters from the output.
- Do not duplicate identical URLs in the same and different cluster
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

def p3_process_web_search_results(certification_info, web_search_json,
                                  current_state=None):
    """
    Process web search results and update current state with 
    relevance-based link management.

    Args:
        certification_info: Certification context
        web_search_json: New web search results
        current_state: Current important links state (optional)

    Returns:
        Prompt for LLM to process and update state
    """
    if current_state is None:
        current_state = {
            "categories": {
                "pdf": {},
                "non-pdf": {}
            }
        }

    return f"""
Current Important Links State:
{json.dumps(current_state, indent=2, ensure_ascii=False)}

Certification Context:
{json.dumps(certification_info, indent=2, ensure_ascii=False)}

New Web Search Results:
{json.dumps(web_search_json, indent=2, ensure_ascii=False)}

Task - State-Based Link Update:
1. Extract ALL clickable links from the new web search results markdown content
2. For each new link, analyze its relevance to the certification (importance 1-10)
3. Filter to include only links with importance >=7
4. Categorize by functional cluster AND file type (PDF vs non-PDF)
5. Add all qualifying links (importance >=7) to the appropriate clusters
   - Simply add links to their correct category and file type cluster
   - No comparison with existing links needed - just keep adding
6. Ensure proper clustering - links must be in the correct category based on 
   their function
7. Return updated state with the same JSON structure

Output Requirements:
- Maintain exact JSON schema structure as current state
- Update only clusters that have changes
- Keep existing high-relevance links unless replaced by higher-relevance ones
- Ensure all links are properly clustered by function and file type
- Include reasoning for any link replacements or additions

Focus on:
- Links embedded in the markdown content of search results
- URL, title, and description from each web result
- Creating meaningful descriptions for links without clear context
- Maintaining link quality through relevance-based filtering"""


# ============================================================================
# Pipeline 4: Aggregation Prompts
# ============================================================================

SYSTEM_PROMPT_P4_PARAMETER = """
You are an expert structured data reconciler for certifications.

TASK
Given multiple candidate JSON entries for the same certification, reconcile them into a single, clean record. Compare all entries, remove duplication, resolve conflicts, and fill ONLY the fields in the target schema. Output STRICT JSON ONLY in the exact target schema (all keys present).

TARGET SCHEMA (types):
{
  "artifact_type": string | null,                      // enum: product_certification | management_system_certification | registration | market_access_authorisation | shipment_document
  "name": string | null,
  "aliases": string[],                                 // 0–5; dedup, case-insensitive
  "issuing_body": string | null,
  "region": string | null,                             // one of: "EU/EEA" | "United States" | "Global" | "China Mainland"
  "mandatory": boolean | null,
  "validity_period_months": number | null,            // 0 = no fixed expiry
  "overview": string | null,                           // ≤ 400 chars
  "full_description": string | null,                   // 80–150 words
  "legal_reference": string | null,                    // e.g., "Directive 2011/65/EU"
  "domain_tags": string[],                             // 1–2; snake_case
  "scope_tags": string[],                              // 0–10; singular nouns, snake_case
  "harmonized_standards": string[],
  "fee": string | null,
  "application_process": string | null,                // ≤ 300 chars; bullets allowed with "1. ", "2. "
  "official_link": string | null,                      // canonical URL
  "updated_at": string | null,                         // ISO-8601 Z
  "sources": string[],                                 // list of URLs used
  "lead_time_days": number | null,
  "processing_time_days": number | null,
  "prerequisites": string[],
  "audit_scope": string[],
  "test_items": string[],
  "other_relevant_info": string | null
}

MERGE RULES (very important)
1) Evidence-first: Fill a field only if at least one input entry explicitly supports it. Never guess.
2) Conflict resolution priority:
   - legal_reference & official_link: prefer primary law texts (e.g., EUR-Lex) over summaries; prefer consolidated/canonical links.
   - name: prefer official title from governing body; include long form; add short forms to aliases.
   - artifact_type: map consistently via the enum; for RoHS use "product_certification".
   - region: normalize to one of {EU/EEA, United States, Global, China Mainland}.
   - mandatory: true if law/regulation is required for market access; otherwise false.
   - validity_period_months: 0 if no fixed renewal stated.
3) Scalars (string/number/bool):
   - If consistent across entries → use that value.
   - If conflicting → choose the most authoritative source (official/EUR-Lex over secondary portals). If still ambiguous → leave null.
4) Arrays (aliases, tags, standards, sources, etc.):
   - Union + strict de-dup (case-insensitive, trim spaces).
   - aliases: limit to top 5 most common/official; prefer canonical spellings; drop duplicates like “RoHS” vs “rohs”.
   - domain_tags: 1–2 items max; snake_case (e.g., environmental_compliance, chemical_safety).
   - scope_tags: singular snake_case (e.g., electronic_equipment, medical_device).
5) Text fields:
   - overview ≤ 400 chars; plain language.
   - full_description 80–150 words; concise, factual; no marketing language.
   - application_process ≤ 300 chars; short steps or a pointer URL.
6) URLs:
   - Keep HTTPS; prefer official/canonical (eur-lex.europa.eu, environment.ec.europa.eu, echa.europa.eu).
   - sources must include every used URL from inputs (dedup).
   - official_link must be a single canonical URL for the certification landing or law.
7) Dates:
   - updated_at: if provided, keep the **most recent** ISO-8601 Z from inputs; otherwise leave null (the caller may set it later).
8) test_items:
   - For RoHS, list the restricted substances by canonical names; keep snake_case (e.g., hexavalent_chromium, bis(2-ethylhexyl)_phthalate).
9) Do NOT add fields beyond the schema. If something is unknown, leave null or [].

OUTPUT
- STRICT JSON ONLY, exactly the target schema with all keys present.
- No prose, no markdown, no code fences.
"""