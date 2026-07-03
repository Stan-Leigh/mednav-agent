from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("MedNav Stdio Server")

# Mock database of clinical trials
CLINICAL_TRIALS_DB = [
    {
        "nct_id": "NCT01234567",
        "title": "Efficacy and Safety Study of Drug X in Patients with Mild to Moderate Hypertension",
        "condition": "Hypertension",
        "phase": "Phase 3",
        "status": "Recruiting",
        "eligibility_criteria": "Inclusion: Age 18-65; diagnosed with mild-to-moderate hypertension; not taking other blood pressure medications.\nExclusion: History of stroke or heart attack; pregnant or lactating.",
        "description": "This study evaluates whether Drug X is superior to placebo in lowering systolic blood pressure over 12 weeks."
    },
    {
        "nct_id": "NCT02345678",
        "title": "A Phase 2 Study of Therapy Y for Stage III Non-Small Cell Lung Cancer",
        "condition": "Non-Small Cell Lung Cancer",
        "phase": "Phase 2",
        "status": "Active, not recruiting",
        "eligibility_criteria": "Inclusion: Age >= 18; histologically confirmed Stage III NSCLC; previous chemotherapy completed.\nExclusion: Active brain metastases; severe autoimmune disease.",
        "description": "This study assesses the overall survival and progression-free survival of patients receiving Therapy Y."
    },
    {
        "nct_id": "NCT03456789",
        "title": "Evaluation of Dietary Intervention Z in Pediatric Type 1 Diabetes",
        "condition": "Type 1 Diabetes",
        "phase": "Phase 1",
        "status": "Completed",
        "eligibility_criteria": "Inclusion: Age 6-12; diagnosed with Type 1 Diabetes within the last 12 months.\nExclusion: Undergoing other experimental dietary regimens.",
        "description": "This trial evaluates safety and compliance of dietary supplement Z in young patients."
    }
]

# Mock medical glossary
MEDICAL_GLOSSARY = {
    "myocardial infarction": "A heart attack. This occurs when blood flow to a part of the heart is blocked, causing damage to the heart muscle.",
    "hypertension": "High blood pressure. A common condition in which the long-term force of the blood against your artery walls is high enough that it may eventually cause health problems, such as heart disease.",
    "erythema": "Redness of the skin, usually caused by increased blood flow in superficial capillaries (often due to inflammation, infection, or injury).",
    "dyspnea": "Shortness of breath or difficulty breathing.",
    "metastasis": "The spread of cancer cells from the original site to other parts of the body.",
    "benign": "Not cancerous. A benign tumor does not invade nearby tissue or spread to other parts of the body.",
    "malignant": "Cancerous. A malignant tumor has the capacity to invade surrounding tissues and spread throughout the body."
}

@mcp.tool()
def search_clinical_trials(query: str) -> str:
    """Search for clinical trials by condition or keyword.
    
    Args:
        query: Search term (e.g. 'Hypertension', 'Lung Cancer', 'Diabetes')
    """
    query_lower = query.lower()
    results = []
    for trial in CLINICAL_TRIALS_DB:
        if (query_lower in trial["condition"].lower() or 
            query_lower in trial["title"].lower() or 
            query_lower in trial["description"].lower()):
            results.append({
                "nct_id": trial["nct_id"],
                "title": trial["title"],
                "condition": trial["condition"],
                "phase": trial["phase"],
                "status": trial["status"]
            })
    if not results:
        return f"No clinical trials found matching query '{query}'."
    return json.dumps(results, indent=2)

@mcp.tool()
def get_trial_details(nct_id: str) -> str:
    """Retrieve full details of a specific clinical trial by its NCT ID.
    
    Args:
        nct_id: The NCT ID of the trial (e.g. 'NCT01234567')
    """
    for trial in CLINICAL_TRIALS_DB:
        if trial["nct_id"].upper() == nct_id.upper():
            return json.dumps(trial, indent=2)
    return f"Trial with NCT ID '{nct_id}' not found."

@mcp.tool()
def explain_medical_term(term: str) -> str:
    """Get a simple explanation of a medical jargon term from the medical dictionary.
    
    Args:
        term: The medical term to explain (e.g. 'myocardial infarction')
    """
    term_lower = term.lower().strip()
    if term_lower in MEDICAL_GLOSSARY:
        return MEDICAL_GLOSSARY[term_lower]
    for k, v in MEDICAL_GLOSSARY.items():
        if k in term_lower or term_lower in k:
            return f"{k.title()}: {v}"
    return f"Term '{term}' not found in local dictionary, but you should simplify it for the patient using general knowledge."

if __name__ == "__main__":
    mcp.run()
