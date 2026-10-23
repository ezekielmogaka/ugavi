import json
import re
import sys
from pathlib import Path


KENYA_REGIONS = {"ke-nairobi-primary", "ke-nairobi-dr"}
TENANT_ID = re.compile(r"^[a-z][a-z0-9-]{2,39}$")


def validate(manifest):
    errors = []
    tenants = manifest.get("tenants", [])
    if not tenants:
        errors.append("at least one tenant is required")
    if len(tenants) > 50:
        errors.append("manifest exceeds the validated two-year ceiling of 50 tenants")

    unique_fields = ("tenant_id", "site_name", "compose_project", "http_port")
    for fieldname in unique_fields:
        values = [tenant.get(fieldname) for tenant in tenants]
        duplicates = sorted({value for value in values if value and values.count(value) > 1})
        if duplicates:
            errors.append(f"{fieldname} must be unique: {', '.join(map(str, duplicates))}")

    for index, tenant in enumerate(tenants, start=1):
        prefix = f"tenant {index}"
        missing = [
            fieldname
            for fieldname in (*unique_fields, "primary_region", "dr_region")
            if not tenant.get(fieldname)
        ]
        if missing:
            errors.append(f"{prefix} missing: {', '.join(missing)}")
            continue
        if not TENANT_ID.fullmatch(tenant["tenant_id"]):
            errors.append(f"{prefix} tenant_id must be a lowercase DNS-safe slug")
        if tenant["compose_project"] != f"ugavi-{tenant['tenant_id']}":
            errors.append(
                f"{prefix} compose_project must be ugavi-{tenant['tenant_id']}"
            )
        if tenant["primary_region"] not in KENYA_REGIONS:
            errors.append(f"{prefix} primary_region must be Kenya-hosted")
        if tenant["dr_region"] not in KENYA_REGIONS:
            errors.append(f"{prefix} dr_region must be Kenya-hosted")
        if tenant["primary_region"] == tenant["dr_region"]:
            errors.append(f"{prefix} primary and DR locations must differ")
        port = tenant["http_port"]
        if not isinstance(port, int) or not 1024 <= port <= 65535:
            errors.append(f"{prefix} http_port must be an integer from 1024 to 65535")
    return errors


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: python3 deploy/validate_tenant_manifest.py <manifest.json>"
        )
    path = Path(sys.argv[1])
    manifest = json.loads(path.read_text())
    errors = validate(manifest)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(1)
    print(
        json.dumps(
            {"valid": True, "tenant_count": len(manifest["tenants"])}, indent=2
        )
    )


if __name__ == "__main__":
    main()
