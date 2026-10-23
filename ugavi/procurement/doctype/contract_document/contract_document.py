"""Contract Document Repository Controller (GA-009 - CT4).

Central repository for all contract-related documents:
- Signed contract PDF
- Performance bonds/guarantees
- Insurance certificates
- Amendments and variations
- Completion certificates
- Retention release documents
"""
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date
from typing import List, Dict


class ContractDocument(Document):
    pass


def add_contract_document(contract: str, document_type: str,
                          document_file: str, description: str = None,
                          expiry_date: str = None, tags: List[str] = None) -> str:
    """Add a document to the contract repository."""
    doc = frappe.get_doc({
        "doctype": "Contract Document",
        "contract": contract,
        "document_type": document_type,
        "document_file": document_file,
        "description": description,
        "expiry_date": expiry_date,
        "upload_date": now_datetime(),
        "tags": ",".join(tags) if tags else "",
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def get_contract_documents(contract: str, document_type: str = None) -> List[Dict]:
    """Retrieve all documents for a contract, optionally filtered by type."""
    filters = {"contract": contract}
    if document_type:
        filters["document_type"] = document_type
    return frappe.get_all("Contract Document",
        filters=filters,
        fields=["name", "document_type", "description", "document_file",
                "upload_date", "expiry_date", "tags"],
        order_by="upload_date desc",
    )


def get_document_checklist(contract: str) -> Dict:
    """Return checklist of required vs. present documents for a contract."""
    required = {
        "Signed Contract": "Mandatory",
        "Performance Bond": "Mandatory (>500k)",
        "Insurance Certificate": "Mandatory",
        "Tax Compliance Certificate": "Mandatory",
        "Final Acceptance Certificate": "Required at completion",
        "Retention Release Order": "Required at retention expiry",
    }
    present = frappe.get_all("Contract Document",
        filters={"contract": contract},
        fields=["document_type"],
        pluck="document_type",
    )
    checklist = {}
    for doc_type, requirement in required.items():
        checklist[doc_type] = {
            "required": requirement,
            "present": doc_type in present,
            "status": "✅" if doc_type in present else "❌",
        }
    return {
        "contract": contract,
        "total_required": len(required),
        "total_present": sum(1 for v in checklist.values() if v["present"]),
        "documents": checklist,
        "complete": all(v["present"] for v in checklist.values()
                        if v["required"] == "Mandatory"),
    }


def flag_expiring_documents():
    """Scheduled task: alert for contract documents expiring within 30 days."""
    cutoff = add_to_date(now_datetime(), days=30)
    expiring = frappe.get_all("Contract Document",
        filters={"expiry_date": ["between", [now_datetime(), cutoff]]},
        fields=["name", "contract", "document_type", "expiry_date"],
    )
    for doc in expiring:
        frappe.log_error(
            title="Contract Document Expiring",
            message=f"{doc.document_type} for {doc.contract} expires on {doc.expiry_date}"
        )
    return len(expiring)


def get_missing_documents_summary() -> List[Dict]:
    """Get all active contracts with missing required documents."""
    active_contracts = frappe.get_all("Ugavi Contract",
        filters={"status": ["in", ["Active", "In Progress"]]},
        fields=["name", "supplier", "contract_value"],
    )
    missing = []
    for c in active_contracts:
        checklist = get_document_checklist(c.name)
        if not checklist["complete"]:
            missing_docs = [k for k, v in checklist["documents"].items()
                           if not v["present"] and v["required"] == "Mandatory"]
            missing.append({
                "contract": c.name,
                "supplier": c.supplier,
                "value": c.contract_value,
                "missing_documents": missing_docs,
            })
    return missing