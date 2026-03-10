"""Hardcoded mock files per connector provider for demo/dev use."""

MOCK_FILES_BY_PROVIDER: dict[str, list[dict]] = {
    "onedrive": [
        {
            "name": "Sunrise Senior Living - Rent Roll Q4 2025.xlsx",
            "path": "/Starwood Capital/Senior Housing/Sunrise Senior Living/Rent Roll Q4 2025.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "Sunrise Senior Living — Rent Roll as of December 31, 2025\n"
                "Property: 450 Oak Park Blvd, Scottsdale, Arizona (AZ) 85251\n"
                "Total Units: 142 (68 IL, 52 AL, 22 MC)\n"
                "Average Monthly Rate: IL $4,850, AL $7,200, MC $9,750\n"
                "Occupancy: 91.5% overall (IL 95%, AL 89%, MC 86%)\n"
                "Total Monthly Revenue: $892,340\n"
                "Concessions Outstanding: 3 units at 10% discount, expiring March 2026"
            ),
        },
        {
            "name": "Meridian Land Dev - Financial Statement 2025.pdf",
            "path": "/Starwood Capital/Land Development/Meridian/Financial Statement 2025.pdf",
            "file_type": "pdf",
            "text_content": (
                "Meridian Master-Planned Community — Annual Financial Statement FY2025\n"
                "Location: 12800 N Meridian Rd, Surprise, Arizona (AZ) 85379 (680 acres)\n"
                "Lots Sold YTD: 312 of 1,450 total planned (21.5% absorption)\n"
                "Average Lot Price: $185,000 | Revenue YTD: $57.7M\n"
                "Infrastructure Spend: $22.4M (Phase 2 roads, water, sewer)\n"
                "Net Operating Income: $18.3M | Remaining Entitlement: 1,138 lots\n"
                "Builder Contracts: Toll Brothers (180 lots), Meritage (95 lots), Taylor Morrison (120 lots)"
            ),
        },
        {
            "name": "Azure Residences - Purchase Agreement Draft.pdf",
            "path": "/Starwood Capital/Luxury Condo/Azure Residences/Purchase Agreement Draft v3.pdf",
            "file_type": "pdf",
            "text_content": (
                "PURCHASE AND SALE AGREEMENT — Azure Residences, 2200 Collins Ave, Miami Beach, FL 33139\n"
                "Seller: Azure Development Group LLC | Buyer: Starwood Capital Fund XIV\n"
                "Purchase Price: $187,500,000 (42 luxury condo units, avg $4.46M/unit)\n"
                "Earnest Money Deposit: $9,375,000 (5%) due within 5 business days\n"
                "Due Diligence Period: 45 days from execution\n"
                "Estimated Closing Date: April 15, 2026\n"
                "Seller Representations: 94% pre-sold, 3 units pending contract execution"
            ),
        },
        {
            "name": "Portfolio Operating Budget 2026.xlsx",
            "path": "/Starwood Capital/Portfolio/Operating Budget 2026.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "Starwood Capital — Consolidated Portfolio Operating Budget 2026\n"
                "Total Properties: 28 | Total Units: 6,840 | AUM: $2.1B\n"
                "Budgeted Revenue: $412M (+4.2% YoY) | Budgeted OpEx: $198M\n"
                "NOI Budget: $214M | Target NOI Margin: 51.9%\n"
                "CapEx Reserve: $34.5M (avg $5,044/unit)\n"
                "Key Assumptions: 3.5% rent growth, 93% avg occupancy, 2.8% expense inflation\n"
                "Risk Factors: Insurance +12% (FL/TX coastal), property tax appeals pending in 4 jurisdictions"
            ),
        },
        {
            "name": "Quarterly Investor Report Q3 2025.pdf",
            "path": "/Starwood Capital/Investor Relations/Quarterly Report Q3 2025.pdf",
            "file_type": "pdf",
            "text_content": (
                "Starwood Capital Real Estate Fund XIV — Q3 2025 Investor Report\n"
                "Fund Size: $3.2B | Deployed Capital: $2.4B (75%)\n"
                "Gross IRR (Since Inception): 18.7% | Net IRR: 14.2%\n"
                "Equity Multiple: 1.6x | DPI: 0.3x\n"
                "New Acquisitions Q3: 3 properties totaling $340M (Phoenix MF, Dallas Industrial, Miami Condo)\n"
                "Dispositions Q3: 1 property ($92M, Atlanta Office — 2.1x MOIC)\n"
                "Portfolio Occupancy: 93.8% | Same-Store NOI Growth: +5.1% YoY"
            ),
        },
    ],
    "box": [
        {
            "name": "Greystone Portfolio Model v2.xlsx",
            "path": "/Bain Capital RE/Models/Greystone Portfolio Model v2.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "Greystone Multifamily Portfolio — Acquisition Model (10-Year DCF)\n"
                "Portfolio: 8 properties, 2,340 units across TX and GA\n"
                "Acquisition Price: $385M ($164,530/unit) | Going-In Cap Rate: 5.2%\n"
                "Year 1 NOI: $20.0M | Stabilized NOI (Yr 3): $23.8M\n"
                "Exit Cap Rate: 5.5% | Projected Exit Value: $432M (Yr 7)\n"
                "Levered IRR: 16.4% | Equity Multiple: 2.1x\n"
                "Financing: $269.5M (70% LTV), 5.8% fixed rate, 7-year term, 2-year IO"
            ),
        },
        {
            "name": "Austin Rent Comps Analysis.xlsx",
            "path": "/Bain Capital RE/Market Research/Austin Rent Comps Q4 2025.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "Austin Multifamily Rent Comparable Analysis — Q4 2025\n"
                "Subject: The Domain at Mueller, 4200 Mueller Blvd, Austin, TX 78723\n"
                "Comp Set: 12 Class A properties within 3-mile radius\n"
                "Subject Avg Rent: $1,875/unit | Market Avg: $1,920/unit (2.4% below market)\n"
                "Subject Occupancy: 92.3% | Market Avg: 94.1%\n"
                "Avg Rent PSF: Subject $2.42 vs Market $2.51\n"
                "New Supply Pipeline: 3,200 units delivering 2026 (4.8% inventory growth)\n"
                "Rent Growth Forecast: 2.5-3.0% (2026), decelerating from 4.1% (2025)"
            ),
        },
        {
            "name": "IC Memo - Crossroads Industrial.pdf",
            "path": "/Bain Capital RE/Investment Committee/IC Memo - Crossroads Industrial Park.pdf",
            "file_type": "pdf",
            "text_content": (
                "INVESTMENT COMMITTEE MEMORANDUM — Crossroads Industrial Park\n"
                "Location: 8900 I-35 Corridor, San Marcos, TX 78666 (42 acres, 580,000 SF)\n"
                "Proposed Acquisition: $78.5M ($135/SF) from Prologis divestiture\n"
                "In-Place NOI: $4.7M (6.0% cap rate) | Mark-to-Market Opportunity: +18%\n"
                "Tenant Roster: Amazon (38% NRA, exp 2029), FedEx (22%), Home Depot (15%)\n"
                "Value-Add Plan: Lease-up 48,000 SF vacancy + 12,000 SF expansion, $4.2M CapEx\n"
                "Stabilized NOI: $5.9M (7.5% yield on cost) | Target Exit: $98M (Yr 5, 5.75% cap)"
            ),
        },
        {
            "name": "Fund III Performance Summary.pdf",
            "path": "/Bain Capital RE/Investor Relations/Fund III Performance Summary 2025.pdf",
            "file_type": "pdf",
            "text_content": (
                "Bain Capital Real Estate Fund III — Performance Summary as of September 30, 2025\n"
                "Fund Vintage: 2021 | Committed Capital: $1.8B | Called: 92%\n"
                "Gross MOIC: 1.45x | Net IRR: 12.8% | DPI: 0.42x\n"
                "Realized Investments: 6 of 19 (avg 1.7x MOIC)\n"
                "Unrealized Portfolio: 13 assets, $1.2B invested equity\n"
                "Sector Allocation: Multifamily 45%, Industrial 30%, Life Science 15%, Other 10%\n"
                "Geographic Focus: Sun Belt 65%, Northeast 20%, West Coast 15%"
            ),
        },
    ],
    "google_drive": [
        {
            "name": "Phoenix Multifamily Market Report 2025.pdf",
            "path": "/Market Research/Southwest/Phoenix Multifamily Market Report 2025.pdf",
            "file_type": "pdf",
            "text_content": (
                "Phoenix Metropolitan Multifamily Market Report — Year-End 2025\n"
                "Total Inventory: 298,400 units | Vacancy Rate: 7.2% (down from 8.1% YoY)\n"
                "Average Asking Rent: $1,485/unit (+3.8% YoY) | Effective Rent: $1,420\n"
                "Net Absorption: 12,800 units (2025) vs 18,200 units delivered\n"
                "Cap Rate Range: 4.75-5.50% (Class A), 5.25-6.25% (Class B)\n"
                "Top Submarkets: Scottsdale ($1,890 avg), Tempe ($1,620), Gilbert ($1,540)\n"
                "2026 Outlook: 14,500 units in pipeline, rent growth expected 2.5-3.5%"
            ),
        },
        {
            "name": "Inland Empire Industrial Deep Dive.pdf",
            "path": "/Market Research/West Coast/Inland Empire Industrial Deep Dive Q4 2025.pdf",
            "file_type": "pdf",
            "text_content": (
                "Inland Empire Industrial Market — Deep Dive Analysis Q4 2025\n"
                "Total Inventory: 612M SF | Vacancy: 5.8% (up from 3.2% in 2023)\n"
                "Average NNN Rent: $1.12/SF/mo ($13.44/SF/yr) — down 4% from peak\n"
                "Net Absorption: 18.4M SF (2025) vs 24.6M SF new deliveries\n"
                "Major Tenants: Amazon (28M SF), UPS (8.5M SF), FedEx (6.2M SF)\n"
                "Construction Pipeline: 15.2M SF under construction, 60% pre-leased\n"
                "Investment Sales: $4.8B total volume (2025), avg cap rate 5.1%\n"
                "Logistics Demand Drivers: E-commerce growth +11%, port volume +6% YoY"
            ),
        },
        {
            "name": "Denver Office Submarket Tracker.xlsx",
            "path": "/Market Research/Mountain West/Denver Office Submarket Tracker 2025.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "Denver Office Submarket Performance Tracker — Q4 2025\n"
                "Total Market: 98.2M SF | Overall Vacancy: 18.4% | Availability: 22.1%\n"
                "Downtown: 24.6M SF, 21.2% vacancy, $38.50/SF gross avg rent\n"
                "Cherry Creek: 4.8M SF, 9.8% vacancy, $42.00/SF (tightest submarket)\n"
                "RiNo/River North: 3.2M SF, 14.5% vacancy, $36.75/SF, strong tenant demand\n"
                "DTC/Southeast: 18.4M SF, 19.8% vacancy, $32.00/SF, sublease overhang\n"
                "Net Absorption YTD: -1.2M SF | Sublease Availability: 4.8M SF (4.9% of stock)"
            ),
        },
        {
            "name": "Nashville Multifamily Supply Forecast.pdf",
            "path": "/Market Research/Southeast/Nashville Multifamily Supply Forecast 2026-2028.pdf",
            "file_type": "pdf",
            "text_content": (
                "Nashville MSA Multifamily Supply Forecast 2026-2028\n"
                "Current Inventory: 142,600 units | Under Construction: 18,400 units\n"
                "2026 Deliveries (Projected): 11,200 units | 2027: 7,800 | 2028: 4,200\n"
                "Peak Supply Impact: Mid-2026, vacancy expected to reach 8.5%\n"
                "Demand Drivers: 85 net new residents/day, healthcare/tech job growth +3.2%\n"
                "Submarket Hotspots: Germantown, The Gulch, East Nashville, Antioch\n"
                "Rent Forecast: Flat to -1% (2026), recovery +2-3% (2027-2028)"
            ),
        },
    ],
    "sharepoint": [
        {
            "name": "Quarterly Investor Report Template.docx",
            "path": "/Templates/Investor Relations/Quarterly Investor Report Template.docx",
            "file_type": "docx",
            "text_content": (
                "QUARTERLY INVESTOR REPORT TEMPLATE — [Fund Name] [Quarter] [Year]\n"
                "Section 1: Executive Summary (fund performance, key events, outlook)\n"
                "Section 2: Portfolio Overview (property count, occupancy, NOI, CapEx)\n"
                "Section 3: Investment Activity (acquisitions, dispositions, pipeline)\n"
                "Section 4: Financial Summary (IRR, equity multiple, DPI, cash yield)\n"
                "Section 5: Market Commentary (macro trends, sector outlook, risk factors)\n"
                "Appendix A: Property-Level Detail | Appendix B: Waterfall Distribution Schedule"
            ),
        },
        {
            "name": "Due Diligence Checklist - Acquisition.xlsx",
            "path": "/Templates/Acquisitions/Due Diligence Checklist - Acquisition.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "ACQUISITION DUE DILIGENCE CHECKLIST — [Property Name]\n"
                "Phase 1 (Week 1-2): Title & Survey, Environmental Phase I, Zoning Verification\n"
                "Phase 2 (Week 2-3): Rent Roll Audit, Lease Abstract Review, Tenant Interviews\n"
                "Phase 3 (Week 3-4): Property Condition Assessment, Deferred Maintenance Estimate\n"
                "Phase 4 (Week 4-5): Financial Underwriting, Tax Return Review, Insurance Analysis\n"
                "Phase 5 (Week 5-6): Legal Review, Entity Structuring, Lender Coordination\n"
                "Sign-Off Required: Acquisitions Lead, Asset Management, Legal, Fund Controller"
            ),
        },
        {
            "name": "Asset Management Monthly Report Template.xlsx",
            "path": "/Templates/Asset Management/Monthly Report Template.xlsx",
            "file_type": "xlsx",
            "text_content": (
                "MONTHLY ASSET MANAGEMENT REPORT — [Property Name] [Month] [Year]\n"
                "KPIs: Occupancy %, Revenue vs Budget, NOI vs Budget, CapEx Spend\n"
                "Leasing Activity: New Leases, Renewals, Move-Outs, Pending Applications\n"
                "Maintenance: Work Orders (Open/Closed), Emergency Repairs, Preventive Schedule\n"
                "Financial: Actual vs Budget Variance, Collections Rate, Delinquency Tracking\n"
                "Market: Comp Survey Update, Concession Tracking, Competitor Occupancy\n"
                "Action Items: Outstanding Issues, Upcoming Lease Expirations, Capital Projects"
            ),
        },
        {
            "name": "Investment Memo Template.docx",
            "path": "/Templates/Investment Committee/Investment Memo Template.docx",
            "file_type": "docx",
            "text_content": (
                "INVESTMENT COMMITTEE MEMORANDUM TEMPLATE — [Deal Name]\n"
                "Executive Summary: Property overview, investment thesis, pricing summary\n"
                "Market Analysis: Submarket fundamentals, supply/demand, rent trends\n"
                "Financial Analysis: Going-in yield, stabilized NOI, DCF returns (IRR, EM)\n"
                "Risk Assessment: Key risks (market, execution, regulatory), mitigants\n"
                "Comparable Transactions: Recent sales, cap rate benchmarks, price/unit or PSF\n"
                "Recommendation: Proceed / Pass / Request Additional Diligence"
            ),
        },
    ],
}
