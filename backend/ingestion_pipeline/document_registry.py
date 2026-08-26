# document_registry.py
# Canonical document registry mapping files to metadata entries.

DOCUMENT_REGISTRY = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "document_id": "support_policy_v3",
        "document_name": "ParcelPilot Support Policy v3",
        "document_type": "support_policy",
        "status": "CURRENT",
        "effective_date": "2026-05-01",
        "authority_level": 80,
        "account_id": None,
        "retrieval_enabled": True
    },

    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "document_id": "support_policy_v2",
        "document_name": "ParcelPilot Support Policy v2",
        "document_type": "support_policy",
        "status": "DEPRECATED",
        "effective_date": "2025-01-01",
        "authority_level": 0,
        "account_id": None,
        "retrieval_enabled": False
    },

    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "document_id": "cancellation_service_credit_sop_v4",
        "document_name": "ParcelPilot Cancellation and Service Credit SOP v4",
        "document_type": "sop",
        "status": "CURRENT",
        "effective_date": "2026-06-15",
        "authority_level": 80,
        "account_id": None,
        "retrieval_enabled": True
    },

    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "document_id": "product_operations_guide",
        "document_name": "ParcelPilot Product Operations Guide",
        "document_type": "product_documentation",
        "status": "CURRENT",
        "authority_level": 70,
        "account_id": None,
        "retrieval_enabled": True
    },

    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "document_id": "northstar_agreement",
        "document_name": "Northstar Logistics Enterprise Agreement",
        "document_type": "customer_agreement",
        "status": "ACTIVE",
        "account_id": "ACCT-001",
        "customer_name": "Northstar Logistics",
        "authority_level": 100,
        "retrieval_enabled": True
    },

    "06_LumenWorks_Service_Agreement.pdf": {
        "document_id": "lumenworks_agreement",
        "document_name": "LumenWorks Service Agreement",
        "document_type": "customer_agreement",
        "status": "ACTIVE",
        "account_id": "ACCT-002",
        "customer_name": "LumenWorks",
        "authority_level": 100,
        "retrieval_enabled": True
    }
}
