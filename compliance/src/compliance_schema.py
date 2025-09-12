from pydantic import BaseModel
from typing import List, Optional, Literal

class Compliance(BaseModel):
    artifact_type: Literal[
        "product_certification",
        "management_system_certification",
        "registration",
        "market_access_authorisation",
        "shipment_document"
    ]
    name: str
    aliases: List[str]
    issuing_body: str
    region: Literal["EU/EEA", "United States", "Global", "China Mainland", "Other"]
    mandatory: str
    validity_period: str
    overview: str
    full_description: str
    legal_reference: Optional[str]
    domain_tags: List[Literal["Product", "Safety", "Environment", "CSR", "Other"]]
    scope_tags: List[str]
    harmonized_standards: List[str]
    fee: Optional[str]
    application_process: Optional[str]
    official_link: Optional[str]
    updated_at: str  # ISO-8601 datetime
    sources: List[str]
    processing_time: Optional[str]
    prerequisites: List[str]
    audit_scope: List[str]
    test_items: List[str]
    other_relevant_info: List[str]
