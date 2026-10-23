"""E2E test fixtures for Ugavi."""
import pytest
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def pr_data():
    """Sample Purchase Requisition data for e2e tests."""
    return {
        "title": "Test PR — Office Supplies",
        "donor": "USAID",
        "department": "Administration",
        "items": [
            {"item_code": "PAPER-001", "item_name": "A4 Paper", "quantity": 100, "estimated_unit_price": 500},
            {"item_code": "TONER-001", "item_name": "Printer Toner", "quantity": 5, "estimated_unit_price": 8000},
        ],
        "justification": "Quarterly office supplies restock",
    }


@pytest.fixture
def tender_data():
    """Sample Tender data for e2e tests."""
    return {
        "title": "Test Tender — Medical Supplies",
        "donor": "Global Fund",
        "procurement_method": "Open Tender",
        "estimated_value": 1500000,
        "submission_deadline": frappe.utils.add_days(frappe.utils.now_datetime(), 14),
        "opening_officer_1": "opening1@ugavi.demo",
        "opening_officer_2": "opening2@ugavi.demo",
        "opening_officer_3": "opening3@ugavi.demo",
    }


@pytest.fixture
def bid_data():
    """Sample Bid data for e2e tests."""
    return {
        "tender": None,  # Set at test time
        "supplier": "SUP-001",
        "status": "Draft",
    }


@pytest.fixture
def doa_data():
    """Sample Delegation of Authority entries."""
    return [
        {"role": "Approver Level 1", "amount_limit": 500000, "department": None, "donor": None},
        {"role": "Approver Level 2", "amount_limit": 5000000, "department": None, "donor": None},
        {"role": "Procurement Officer", "amount_limit": 200000, "department": None, "donor": None},
    ]