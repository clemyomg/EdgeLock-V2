# backend/mappings.py

# LEFT: API-Football Name (Exact strings from your logs)
# RIGHT: CSV Name (Stathead format)
NAME_MAP = {
    # --- Top Teams ---
    "Bayern Munich": "Bayern Munich",
    "Bayern München": "Bayern Munich",     # 👈 Added from logs
    "FC Bayern München": "Bayern Munich",
    
    "Borussia Dortmund": "Dortmund",
    "Dortmund": "Dortmund",
    
    "RB Leipzig": "RB Leipzig",
    
    "Bayer 04 Leverkusen": "Leverkusen",
    "Bayer Leverkusen": "Leverkusen",
    
    # --- The Tricky Ones (Umlauts & Prefixes) ---
    "Borussia Mönchengladbach": "M'gladbach", # 👈 Added (with ö)
    "Borussia Monchengladbach": "M'gladbach",
    "M'gladbach": "M'gladbach",
    
    "Eintracht Frankfurt": "Eint Frankfurt",
    "VfL Wolfsburg": "Wolfsburg",
    
    "1899 Hoffenheim": "Hoffenheim",       # 👈 Added from logs
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "TSG Hoffenheim": "Hoffenheim",
    
    "FSV Mainz 05": "Mainz 05",            # 👈 Added from logs
    "1. FSV Mainz 05": "Mainz 05",
    "Mainz 05": "Mainz 05",
    
    "SC Freiburg": "Freiburg",
    "Werder Bremen": "Werder Bremen",
    "FC Augsburg": "Augsburg",
    "Augsburg": "Augsburg",
    
    "VfB Stuttgart": "Stuttgart",
    "VfL Bochum": "Bochum",
    
    "1. FC Heidenheim": "Heidenheim",
    "1. FC Heidenheim 1846": "Heidenheim",
    "Heidenheim": "Heidenheim",
    
    "Union Berlin": "Union Berlin",
    "1. FC Union Berlin": "Union Berlin",
    
    # --- Promoted / Relegated / Others ---
    "Holstein Kiel": "Holstein Kiel",
    "Kieler SV Holstein": "Holstein Kiel",
    
    "FC St. Pauli": "St. Pauli",
    "St. Pauli": "St. Pauli",
    
    "Darmstadt 98": "Darmstadt 98",
    "SV Darmstadt 98": "Darmstadt 98",
    
    "1. FC Koln": "FC Koln",
    "FC Koln": "FC Koln",
    "Köln": "FC Koln",
    "1. FC Köln": "FC Koln",
    
    "Hertha BSC": "Hertha BSC",
    "Hertha Berlin": "Hertha BSC",
    
    "Schalke 04": "Schalke 04",
    "FC Schalke 04": "Schalke 04",
    
    "Fortuna Dusseldorf": "Dusseldorf",
    "Greuther Furth": "Greuther Furth",
    "SpVgg Greuther Fürth": "Greuther Furth"
}