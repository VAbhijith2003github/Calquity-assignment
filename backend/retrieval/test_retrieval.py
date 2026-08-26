# test_retrieval.py
import sys
from pathlib import Path

# Add backend's parent directory to path so we can import from backend package
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.retrieval.document_search import search_documents

def print_results(title: str, results: list):
    print(f"\n==================================================")
    print(f"Scenario: {title}")
    print(f"==================================================")
    if not results:
        print("No results returned.")
        return
        
    for idx, res in enumerate(results):
        meta = res["metadata"]
        print(f"[{idx+1}] Score: {res['score']:.4f} | Chunk ID: {res['chunk_id']}")
        print(f"    Document: {meta.get('document_name')} ({meta.get('document_type')})")
        print(f"    Status: {meta.get('status')} | Account ID: {meta.get('account_id')} | Customer: {meta.get('customer_name')}")
        print(f"    Header Path: {' -> '.join(meta.get('header_path', []))}")
        content_snippet = res["content"].replace("\n", " ").strip()[:100] + "..."
        print(f"    Content Snippet: {content_snippet}")
        print("-" * 50)

def main():
    print("Running retrieval verification against Qdrant Cloud...\n")

    # Scenario 1: General search (no customer account)
    # Expected: general current policies, SOPs, product docs. No deprecated documents, no customer agreements.
    results_gen = search_documents(
        query="What are the severity level definitions and first-response times?",
        account_id=None,
        top_k=3
    )
    print_results("General Search (No Customer Account context)", results_gen)

    # Scenario 2: Search with Northstar Logistics account (ACCT-001)
    # Expected: Northstar agreement chunks + general docs. MUST NOT contain LumenWorks agreements.
    results_northstar = search_documents(
        query="What are the terms for shipment cancellation and credit refunds?",
        account_id="ACCT-001",
        top_k=3
    )
    print_results("Northstar Logistics Search (account_id='ACCT-001')", results_northstar)

    # Scenario 3: Search with LumenWorks account (ACCT-002)
    # Expected: LumenWorks agreement chunks + general docs. MUST NOT contain Northstar agreements.
    results_lumenworks = search_documents(
        query="What are the terms for shipment cancellation and credit refunds?",
        account_id="ACCT-002",
        top_k=3
    )
    print_results("LumenWorks Search (account_id='ACCT-002')", results_lumenworks)

    # Scenario 4: Search allowing Deprecated documents (include_deprecated=True)
    # Expected: May return support_policy_v2 chunks.
    results_deprecated = search_documents(
        query="Find the old historical response targets and severity rules.",
        include_deprecated=True,
        top_k=3
    )
    print_results("Include Deprecated Documents (include_deprecated=True)", results_deprecated)

    # Scenario 5: Filter specifically on SOP document type
    # Expected: returns only cancellation SOP documents
    results_sop = search_documents(
        query="Refund credits for failed pick-ups or delays",
        document_types=["sop"],
        top_k=3
    )
    print_results("Document Type Filter (document_types=['sop'])", results_sop)

if __name__ == "__main__":
    main()
