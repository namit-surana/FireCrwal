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