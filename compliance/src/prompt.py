# ============================================================================
# Agent Prompt: Retrieval for Compliance Documents
# ============================================================================
import json


def system_prompt(compliance_type: json) -> str:
    with open(compliance_type, 'r', encoding='utf-8') as f:
        definitions = json.load(f)
        definitions_block = "\n".join([f"- **{k}** : {v}" for k, v in definitions.items()])
    return f"""
You are an expert in international compliance, product certification, and market access regulations.  
You will be given **webscraped content (markdown)** from a webpage that is relevant to a known certification or authorization scheme.  

---

## Rules:
- The content is **related to a single known certification/authorization scheme**.  
- Extract only details explicitly supported by the content.  
- If a field is not mentioned, set it to `null` (for strings/numbers) or `[]` (for lists).  
- Do **not** invent, be **exact** to webscraped content.  
- All output must conform strictly to the structured schema provided. 

---

## Property Definitions (What you need to extract):
{definitions_block}
 """


def complicance_prompt(content: str) -> str:
    return f"""
Webscraped Content (Markdown):
{content}
"""

# ============================================================================
# Agent Prompt: Aggregation for Compliance Documents
# ============================================================================


def summary_prompt(content):
    return f"""
You are an expert assistant specialized in global certifications, compliance, and international trade regulations.  

You are given a dictionary where:
- Each **key** represents a field of information about a certification.  
- Each **key** contains multiple candidate values (all referring to the same certification).  

### Your Task
1. For each key, compare all candidate values.  
2. Select **exactly ONE final value per key**.  
3. You must only pick one value **directly from the provided list** for that key.  
   - Do NOT invent, paraphrase, or reword.  
   - Do NOT merge multiple values into a new string.  
   - Only choose an existing value.  
4. If all values are empty, inconsistent, or invalid, output `null` for that key.  
5. Output must be a **valid JSON object** with the same keys, each mapped to one chosen value.  

### Input Dictionary
{content}
"""


def collapse_duplicates_prompt(content):
    return f"""
You are an expert in global trade certification and compliance data cleaning.  

You are given a dictionary where:
- Each key represents a field of certification information (e.g., restricted substances, requirements, documents).  
- Each key contains multiple lists of values.  
- The values may include duplicates, capitalization differences, or slightly different representations of the same item.  

### Your Task
1. For each key, merge all values across the lists into **one aggregated list**.  
2. Remove duplicates and semantically equivalent entries.  
   - Example: “lead” and “Lead” → keep only “Lead”.  
   - Example: “Polybrominated biphenyls” and “Polybrominated biphenyls (PBB)” → keep only one, preferably the clearer, more informative version.  
3. Keep all **unique, distinct items** that are not duplicates.  
4. There is **no limit on list size** — keep everything that is unique.  
5. **Do not invent, infer, or add values that are not already present in the provided lists.**  
   - You must only output values that exist in the input dictionary.  
6. Output must be in **valid JSON** format with the same keys, but each mapped to the cleaned aggregated list.  

### Input Dictionary
{content}
"""


def aggregation_search_prompt(content):
    return f"""
You are an expert assistant specialized in global trade certifications and compliance data aggregation.  

You are given a dictionary where:  
- Each key represents a certification field (e.g., restricted_substances, validity, application_process).  
- Each key contains multiple lists of candidate values.  
- The values may contain duplicates, near-duplicates, contradictions, or variations in representation.  

### Your Task
1. **Aggregate Values**
   - Merge all values for each key into one final set.  
   - Do not lose information. Keep all distinct, meaningful entries.  
   - There is no restriction on list size.  

2. **Remove Duplicates**
   - Eliminate exact duplicates and semantically equivalent variants.  
   - Example: “Lead” vs “lead” → keep only “Lead”.  
   - Example: “Polybrominated biphenyls” vs “Polybrominated biphenyls (PBB)” → keep only one, preferring the clearer/more informative form.  

3. **Resolve Contradictions**
   - If values are **contradictory** (e.g., different validity periods, conflicting requirements), you are allowed to use your **search toolkit** to check authoritative online sources.  
   - Choose the most accurate and up-to-date value, discarding the incorrect one.  

4. **Special Case – Application Process**
   - If the key is `application_process`, restructure the aggregated values into a **single string**.  
   - The string must be formatted as an **ordered step sequence**:  
     `"1. ..., 2. ..., 3. ..."`  
   - Deduplicate steps if repeated.  
   - Preserve order if steps are numbered or infer logical order if not.  

5. **Output**
   - Return a valid **JSON object** with the same keys, each mapped to the final aggregated values.  
   - Format:
     - Regular fields → array of strings.  
     - `application_process` → one string with numbered steps.  

---

### **Input Dictionary**
{content}
"""

if __name__ == "__main__":
    print(system_prompt('compliance/src/compliance_definition.json'))