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


def build_prompt(certification_info, urls_batch):
    """Legacy function for backward compatibility"""
    return build_batch_prompt(certification_info, urls_batch)
