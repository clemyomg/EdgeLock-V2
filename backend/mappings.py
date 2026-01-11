# backend/mappings.py

# LEFT: API-Football Name (from logs)
# RIGHT: YOUR CSV Name (verified from file)
NAME_MAP = {
    # --- The Problem Teams (Fixed) ---
    "Borussia Mönchengladbach": "Gladbach",
    "Borussia Monchengladbach": "Gladbach",
    "M'gladbach": "Gladbach",
    "Gladbach": "Gladbach",
    
    "Bayern München": "Bayern Munich",
    "FC Bayern München": "Bayern Munich",
    "Bayern Munich": "Bayern Munich",

    "1899 Hoffenheim": "Hoffenheim",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "TSG Hoffenheim": "Hoffenheim",
    
    "FSV Mainz 05": "Mainz 05",
    "1. FSV Mainz 05": "Mainz 05",
    "Mainz 05": "Mainz 05",

    "Eintracht Frankfurt": "Eint Frankfurt",
    
    # --- The Rest (Verified) ---
    "Borussia Dortmund": "Dortmund",
    "Dortmund": "Dortmund",
    
    "RB Leipzig": "RB Leipzig",
    
    "Bayer 04 Leverkusen": "Leverkusen",
    "Bayer Leverkusen": "Leverkusen",
    
    "VfL Wolfsburg": "Wolfsburg",
    
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
    
    "Holstein Kiel": "Holstein Kiel",
    
    "FC St. Pauli": "St. Pauli",
    "St. Pauli": "St. Pauli",
    
    "Darmstadt 98": "Darmstadt 98",
    
    "1. FC Koln": "FC Koln",
    "FC Koln": "FC Koln",
    "Köln": "FC Koln",
    
    "Hertha BSC": "Hertha BSC",
    "Hertha Berlin": "Hertha BSC"
}