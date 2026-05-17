"""
Rupeya.ai — Initial covered universe.

Curated list of ~100 actively-traded PSX stocks intended to approximate
KSE-100 + selected mid-caps as of mid-2026. The actual KSE-100 composition
is rebalanced semi-annually by PSX; a future task will wire a scraper to
auto-refresh from the official index page.

`is_shariah_compliant` reflects approximate KMI All-Share / KMI-30 status
based on business activity. The formal Shariah screen (AAOIFI ratio recompute
from latest filings, per blueprint Section 4.5) is a separate Phase B3+ task
and may override this initial flag once we have financials.
"""

from __future__ import annotations

from typing import TypedDict


class StockSeed(TypedDict):
    ticker: str
    name: str
    sector: str
    sub_sector: str
    is_shariah_compliant: bool


# fmt: off
UNIVERSE: list[StockSeed] = [
    # ===== Commercial Banks — conventional (NOT Shariah) =====
    {"ticker": "HBL",    "name": "Habib Bank Limited",            "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "MCB",    "name": "MCB Bank Limited",              "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "UBL",    "name": "United Bank Limited",           "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "NBP",    "name": "National Bank of Pakistan",     "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "ABL",    "name": "Allied Bank Limited",           "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "BAFL",   "name": "Bank Alfalah Limited",          "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "BAHL",   "name": "Bank AL Habib Limited",         "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "AKBL",   "name": "Askari Bank Limited",           "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "BOP",    "name": "Bank of Punjab",                "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "JSBL",   "name": "JS Bank Limited",               "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    {"ticker": "HMB",    "name": "Habib Metropolitan Bank",       "sector": "Commercial Banks", "sub_sector": "Banking",                 "is_shariah_compliant": False},
    # Islamic banks (Shariah-compliant)
    {"ticker": "MEBL",   "name": "Meezan Bank Limited",           "sector": "Commercial Banks", "sub_sector": "Islamic Banking",         "is_shariah_compliant": True},
    {"ticker": "FABL",   "name": "Faysal Bank Limited",           "sector": "Commercial Banks", "sub_sector": "Islamic Banking",         "is_shariah_compliant": True},
    {"ticker": "BIPL",   "name": "BankIslami Pakistan Limited",   "sector": "Commercial Banks", "sub_sector": "Islamic Banking",         "is_shariah_compliant": True},
    # DIBPL — Dubai Islamic Bank Pakistan: delisted/private subsidiary; removed from public universe.

    # ===== Fertilizer =====
    {"ticker": "ENGRO",  "name": "Engro Corporation Limited",     "sector": "Conglomerate",     "sub_sector": "Diversified Holding",     "is_shariah_compliant": True},
    {"ticker": "EFERT",  "name": "Engro Fertilizers Limited",     "sector": "Fertilizer",       "sub_sector": "Urea",                    "is_shariah_compliant": True},
    {"ticker": "FFC",    "name": "Fauji Fertilizer Company",      "sector": "Fertilizer",       "sub_sector": "Urea",                    "is_shariah_compliant": True},
    {"ticker": "FFBL",   "name": "Fauji Fertilizer Bin Qasim",    "sector": "Fertilizer",       "sub_sector": "DAP",                     "is_shariah_compliant": True},
    {"ticker": "FATIMA", "name": "Fatima Fertilizer Company",     "sector": "Fertilizer",       "sub_sector": "Urea & CAN",              "is_shariah_compliant": True},

    # ===== Cement =====
    {"ticker": "LUCK",   "name": "Lucky Cement Limited",          "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "DGKC",   "name": "D.G. Khan Cement Company",      "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "KOHC",   "name": "Kohat Cement Company",          "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "MLCF",   "name": "Maple Leaf Cement Factory",     "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "FCCL",   "name": "Fauji Cement Company",          "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "BWCL",   "name": "Bestway Cement Limited",        "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "PIOC",   "name": "Pioneer Cement Limited",        "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "CHCC",   "name": "Cherat Cement Company",         "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "ACPL",   "name": "Attock Cement Pakistan",        "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},
    {"ticker": "GWLC",   "name": "Gharibwal Cement Limited",      "sector": "Cement",           "sub_sector": "Cement",                  "is_shariah_compliant": True},

    # ===== Power =====
    {"ticker": "HUBC",   "name": "Hub Power Company Limited",     "sector": "Power",            "sub_sector": "IPP",                     "is_shariah_compliant": True},
    {"ticker": "KEL",    "name": "K-Electric Limited",            "sector": "Power",            "sub_sector": "Utility",                 "is_shariah_compliant": True},
    {"ticker": "KAPCO",  "name": "Kot Addu Power Company",        "sector": "Power",            "sub_sector": "IPP",                     "is_shariah_compliant": True},
    {"ticker": "NCPL",   "name": "Nishat Chunian Power",          "sector": "Power",            "sub_sector": "IPP",                     "is_shariah_compliant": True},
    {"ticker": "NPL",    "name": "Nishat Power Limited",          "sector": "Power",            "sub_sector": "IPP",                     "is_shariah_compliant": True},
    {"ticker": "PKGP",   "name": "Pakgen Power Limited",          "sector": "Power",            "sub_sector": "IPP",                     "is_shariah_compliant": True},

    # ===== Oil & Gas Exploration =====
    {"ticker": "OGDC",   "name": "Oil & Gas Development Co.",     "sector": "Oil & Gas Exploration", "sub_sector": "Upstream",           "is_shariah_compliant": True},
    {"ticker": "PPL",    "name": "Pakistan Petroleum Limited",    "sector": "Oil & Gas Exploration", "sub_sector": "Upstream",           "is_shariah_compliant": True},
    {"ticker": "POL",    "name": "Pakistan Oilfields Limited",    "sector": "Oil & Gas Exploration", "sub_sector": "Upstream",           "is_shariah_compliant": True},
    {"ticker": "MARI",   "name": "Mari Petroleum Company",        "sector": "Oil & Gas Exploration", "sub_sector": "Upstream",           "is_shariah_compliant": True},

    # ===== Oil & Gas Marketing & Distribution =====
    {"ticker": "PSO",    "name": "Pakistan State Oil",            "sector": "Oil & Gas Marketing", "sub_sector": "OMC",                  "is_shariah_compliant": True},
    {"ticker": "APL",    "name": "Attock Petroleum Limited",      "sector": "Oil & Gas Marketing", "sub_sector": "OMC",                  "is_shariah_compliant": True},
    {"ticker": "SHEL",   "name": "Shell Pakistan Limited",        "sector": "Oil & Gas Marketing", "sub_sector": "OMC",                  "is_shariah_compliant": True},
    {"ticker": "SNGP",   "name": "Sui Northern Gas Pipelines",    "sector": "Oil & Gas Marketing", "sub_sector": "Gas Distribution",     "is_shariah_compliant": True},
    {"ticker": "SSGC",   "name": "Sui Southern Gas Company",      "sector": "Oil & Gas Marketing", "sub_sector": "Gas Distribution",     "is_shariah_compliant": True},

    # ===== Refineries =====
    {"ticker": "ATRL",   "name": "Attock Refinery Limited",       "sector": "Refinery",         "sub_sector": "Refinery",                "is_shariah_compliant": True},
    {"ticker": "NRL",    "name": "National Refinery Limited",     "sector": "Refinery",         "sub_sector": "Refinery",                "is_shariah_compliant": True},
    {"ticker": "PRL",    "name": "Pakistan Refinery Limited",     "sector": "Refinery",         "sub_sector": "Refinery",                "is_shariah_compliant": True},
    # BYCO renamed to CNERGY (Cnergyico PK Limited) several years ago; removed from universe.

    # ===== Technology & Communication =====
    {"ticker": "SYS",    "name": "Systems Limited",               "sector": "Technology & Communication", "sub_sector": "IT Services",   "is_shariah_compliant": True},
    {"ticker": "AVN",    "name": "Avanceon Limited",              "sector": "Technology & Communication", "sub_sector": "Industrial Automation", "is_shariah_compliant": True},
    {"ticker": "TRG",    "name": "TRG Pakistan Limited",          "sector": "Technology & Communication", "sub_sector": "BPO",           "is_shariah_compliant": True},
    {"ticker": "NETSOL", "name": "NetSol Technologies",           "sector": "Technology & Communication", "sub_sector": "IT Services",   "is_shariah_compliant": True},
    {"ticker": "PTC",    "name": "Pakistan Telecommunication",    "sector": "Technology & Communication", "sub_sector": "Telecom",       "is_shariah_compliant": False},
    {"ticker": "AIRLINK","name": "Air Link Communication",        "sector": "Technology & Communication", "sub_sector": "Mobile Distribution", "is_shariah_compliant": True},

    # ===== Food & Personal Care =====
    {"ticker": "NESTLE", "name": "Nestle Pakistan Limited",       "sector": "Food & Personal Care", "sub_sector": "Dairy & Food",        "is_shariah_compliant": True},
    # UNILEVER (Pakistan) delisted ~2020; only UPFL (Unilever Foods) trades; removed for now.
    # EFOODS — Engro Foods delisted after FrieslandCampina acquisition; removed.
    {"ticker": "FFL",    "name": "Fauji Foods Limited",           "sector": "Food & Personal Care", "sub_sector": "Dairy",               "is_shariah_compliant": True},
    {"ticker": "NATF",   "name": "National Foods Limited",        "sector": "Food & Personal Care", "sub_sector": "Packaged Food",       "is_shariah_compliant": True},
    {"ticker": "RMPL",   "name": "Rafhan Maize Products",         "sector": "Food & Personal Care", "sub_sector": "Food Ingredients",    "is_shariah_compliant": True},
    {"ticker": "COLG",   "name": "Colgate-Palmolive Pakistan",    "sector": "Food & Personal Care", "sub_sector": "Personal Care",       "is_shariah_compliant": True},

    # ===== Pharmaceutical =====
    {"ticker": "GLAXO",  "name": "GlaxoSmithKline Pakistan",      "sector": "Pharmaceutical",   "sub_sector": "Pharma",                  "is_shariah_compliant": True},
    {"ticker": "ABBOTT", "name": "Abbott Laboratories Pakistan",  "sector": "Pharmaceutical",   "sub_sector": "Pharma",                  "is_shariah_compliant": True},
    {"ticker": "SEARL",  "name": "Searle Company Limited",        "sector": "Pharmaceutical",   "sub_sector": "Pharma",                  "is_shariah_compliant": True},
    {"ticker": "FEROZ",  "name": "Ferozsons Laboratories",        "sector": "Pharmaceutical",   "sub_sector": "Pharma",                  "is_shariah_compliant": True},
    {"ticker": "AGP",    "name": "AGP Limited",                   "sector": "Pharmaceutical",   "sub_sector": "Pharma",                  "is_shariah_compliant": True},
    {"ticker": "HINOON", "name": "Highnoon Laboratories",         "sector": "Pharmaceutical",   "sub_sector": "Pharma",                  "is_shariah_compliant": True},
    {"ticker": "IBLHL",  "name": "IBL HealthCare Limited",        "sector": "Pharmaceutical",   "sub_sector": "Pharma Distribution",     "is_shariah_compliant": True},
    {"ticker": "SHFA",   "name": "Shifa International Hospitals", "sector": "Pharmaceutical",   "sub_sector": "Healthcare",              "is_shariah_compliant": True},

    # ===== Chemicals =====
    {"ticker": "ICI",    "name": "ICI Pakistan Limited",          "sector": "Chemical",         "sub_sector": "Diversified Chemicals",   "is_shariah_compliant": True},
    {"ticker": "EPCL",   "name": "Engro Polymer & Chemicals",     "sector": "Chemical",         "sub_sector": "Petrochemicals",          "is_shariah_compliant": True},
    {"ticker": "BERGER", "name": "Berger Paints Pakistan",        "sector": "Chemical",         "sub_sector": "Paints",                  "is_shariah_compliant": True},
    {"ticker": "DAWH",   "name": "Dawood Hercules Corporation",   "sector": "Chemical",         "sub_sector": "Diversified Chemicals",   "is_shariah_compliant": True},
    {"ticker": "LOTCHEM","name": "Lotte Chemical Pakistan",       "sector": "Chemical",         "sub_sector": "PTA",                     "is_shariah_compliant": True},
    {"ticker": "SITC",   "name": "Sitara Chemical Industries",    "sector": "Chemical",         "sub_sector": "Caustic Soda",            "is_shariah_compliant": True},

    # ===== Automobile Assembler / Parts =====
    {"ticker": "INDU",   "name": "Indus Motor Company",           "sector": "Automobile Assembler", "sub_sector": "Car Assembler",       "is_shariah_compliant": True},
    {"ticker": "HCAR",   "name": "Honda Atlas Cars Pakistan",     "sector": "Automobile Assembler", "sub_sector": "Car Assembler",       "is_shariah_compliant": True},
    # PSMC — Pak Suzuki Motor delisted after privatization; removed.
    {"ticker": "ATLH",   "name": "Atlas Honda Limited",           "sector": "Automobile Assembler", "sub_sector": "Motorcycle",          "is_shariah_compliant": True},
    {"ticker": "MTL",    "name": "Millat Tractors Limited",       "sector": "Automobile Assembler", "sub_sector": "Tractor",             "is_shariah_compliant": True},
    {"ticker": "AGTL",   "name": "Al-Ghazi Tractors Limited",     "sector": "Automobile Assembler", "sub_sector": "Tractor",             "is_shariah_compliant": True},
    {"ticker": "GTYR",   "name": "General Tyre & Rubber Co",      "sector": "Auto Parts & Accessories", "sub_sector": "Tyres",           "is_shariah_compliant": True},

    # ===== Engineering / Steel =====
    {"ticker": "MUGHAL", "name": "Mughal Iron & Steel Industries","sector": "Engineering",      "sub_sector": "Steel",                   "is_shariah_compliant": True},
    {"ticker": "ASTL",   "name": "Amreli Steels Limited",         "sector": "Engineering",      "sub_sector": "Steel",                   "is_shariah_compliant": True},
    {"ticker": "ISL",    "name": "International Steels Limited",  "sector": "Engineering",      "sub_sector": "Steel",                   "is_shariah_compliant": True},
    {"ticker": "ASL",    "name": "Aisha Steel Mills Limited",     "sector": "Engineering",      "sub_sector": "Steel",                   "is_shariah_compliant": True},
    {"ticker": "INIL",   "name": "International Industries",      "sector": "Engineering",      "sub_sector": "Tubes & Pipes",           "is_shariah_compliant": True},

    # ===== Textile =====
    {"ticker": "ILP",    "name": "Interloop Limited",             "sector": "Textile",          "sub_sector": "Hosiery",                 "is_shariah_compliant": True},
    {"ticker": "NCL",    "name": "Nishat Chunian Limited",        "sector": "Textile",          "sub_sector": "Composite Textile",       "is_shariah_compliant": True},
    {"ticker": "NML",    "name": "Nishat Mills Limited",          "sector": "Textile",          "sub_sector": "Composite Textile",       "is_shariah_compliant": True},
    {"ticker": "GADT",   "name": "Gadoon Textile Mills",          "sector": "Textile",          "sub_sector": "Spinning",                "is_shariah_compliant": True},
    {"ticker": "KTML",   "name": "Kohinoor Textile Mills",        "sector": "Textile",          "sub_sector": "Composite Textile",       "is_shariah_compliant": True},
    {"ticker": "GATM",   "name": "Gul Ahmed Textile Mills",       "sector": "Textile",          "sub_sector": "Composite Textile",       "is_shariah_compliant": True},

    # ===== Transport / Logistics =====
    {"ticker": "PIBTL",  "name": "Pakistan Intl Bulk Terminal",   "sector": "Transport",        "sub_sector": "Port Logistics",          "is_shariah_compliant": True},
    {"ticker": "PNSC",   "name": "Pakistan National Shipping",    "sector": "Transport",        "sub_sector": "Shipping",                "is_shariah_compliant": True},

    # ===== Insurance — conventional (NOT Shariah) =====
    {"ticker": "AICL",   "name": "Adamjee Insurance Company",     "sector": "Insurance",        "sub_sector": "General Insurance",       "is_shariah_compliant": False},
    {"ticker": "EFUG",   "name": "EFU General Insurance",         "sector": "Insurance",        "sub_sector": "General Insurance",       "is_shariah_compliant": False},
    {"ticker": "JGICL",  "name": "Jubilee General Insurance",     "sector": "Insurance",        "sub_sector": "General Insurance",       "is_shariah_compliant": False},

    # ===== Misc =====
    {"ticker": "PACE",   "name": "Pace Pakistan Limited",         "sector": "Real Estate",      "sub_sector": "Real Estate",             "is_shariah_compliant": True},
    {"ticker": "TPL",    "name": "TPL Properties Limited",        "sector": "Real Estate",      "sub_sector": "REIT",                    "is_shariah_compliant": True},
]
# fmt: on


def covered_tickers() -> list[str]:
    """Quick helper: just the ticker symbols."""
    return [s["ticker"] for s in UNIVERSE]
