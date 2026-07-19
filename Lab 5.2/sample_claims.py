"""
Sample claims data for testing the pipeline.
CLM-001 and CLM-003 should pass.
CLM-002 is for an inactive member and should fail validation.
"""

CLAIMS = [
    {
        "claim_id": "CLM-001",
        "narrative": "Office visit level 3 for established patient M-501. "
                     "Patient is active member. Procedure code 99213. Amount: $150.",
        "member_id": "M-501",
        "procedure_code": "99213",
        "amount": 150,
        "member_active": True
    },
    {
        "claim_id": "CLM-002",
        "narrative": "Office visit level 4 for patient M-777. "
                     "Member inactive. Procedure code 99214. Amount: $250.",
        "member_id": "M-777",
        "procedure_code": "99214",
        "amount": 250,
        "member_active": False  # This will cause validation to fail
    },
    {
        "claim_id": "CLM-003",
        "narrative": "Office visit level 5 for established patient M-501. "
                     "Patient is active member. Procedure code 99215. Amount: $300.",
        "member_id": "M-501",
        "procedure_code": "99215",
        "amount": 300,
        "member_active": True
    }
]

COVERED_PROCEDURES = {"99213", "99214", "99215"}
