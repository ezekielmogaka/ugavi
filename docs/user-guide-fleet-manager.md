# User Guide — Fleet Manager

## Role: Fleet Manager
**Can:** Manage vehicles, allocations, trip logs, fuel logs, spare parts
**Cannot:** Access procurement or sealed bids, cross-donor logistics

---

## Daily Workflows

### 1. Vehicle Registration
1. Navigate to **Fleet > Vehicle**
2. Click **New**
3. Fill: Plate No, Make, Model, Donor, assigned warehouse and service date
4. **Save** → Vehicle added to fleet

### 2. Vehicle Allocation
1. Navigate to **Fleet > Vehicle Allocation**
2. Click **New**
3. Select: Vehicle, Driver/User, donor/project, From Date, To Date
4. **Save** → overlapping and open-ended allocations are rejected

### 3. Trip Log
1. Navigate to **Fleet > Trip Log**
2. Click **New**
3. Select the active Vehicle Allocation and enter start/end evidence
4. **Submit** → validates the allocation period and updates odometer evidence

### 4. Fuel Log
1. Navigate to **Fleet > Fuel Log**
2. Click **New**
3. Select an open Fuel Fleet Purchase reconciliation and the vehicle
4. Enter litres, receipt and odometer evidence, then **Submit**
5. The submitted quantity is deducted from the purchased quantity; over-allocation is blocked

### 5. Spare Parts Issue
1. Navigate to **Fleet > Spare Parts Issue**
2. Click **New**
3. Select the donor warehouse, vehicle and open Spare Part purchase row
4. Enter the issue quantity and **Submit**
5. Ugavi creates and stores the exact linked ERPNext Material Issue Stock Entry

---

## Key Rules
- **Vehicle service tracking**: Scheduled task flags vehicles overdue for service (daily check)
- **Fuel efficiency monitoring**: System flags abnormal fuel consumption (>20% deviation from average)
- **Trip authorization**: Every submitted trip must have a matching allocation
- **Purchase reconciliation**: Every fleet-classified receipt/invoice row stays open until fully allocated
- **Donor isolation**: vehicles, source purchases, warehouses and reports must use the same donor
- **Asset link**: Fleet vehicles can link to Asset Register for full lifecycle tracking