# backend/mappings.py

# LEFT: API-Football Name (What comes from the internet)
# RIGHT: CSV Name (What is in your Stathead files)
NAME_MAP = {
    # Top Teams
    "Bayern Munich": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "RB Leipzig": "RB Leipzig",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Bayer Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Eint Frankfurt",
    "VfL Wolfsburg": "Wolfsburg",
    
    # The Tricky Ones (Gladbach, Mainz, etc.)
    "Borussia Monchengladbach": "M'gladbach",
    "M'gladbach": "M'gladbach",
    "Mainz 05": "Mainz 05",
    "1. FSV Mainz 05": "Mainz 05",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "TSG Hoffenheim": "Hoffenheim",
    "SC Freiburg": "Freiburg",
    "Werder Bremen": "Werder Bremen",
    "FC Augsburg": "Augsburg",
    "Augsburg": "Augsburg",
    "VfB Stuttgart": "Stuttgart",
    "VfL Bochum": "Bochum",
    "1. FC Heidenheim": "Heidenheim",
    "Heidenheim": "Heidenheim",
    "Union Berlin": "Union Berlin",
    
    # Relegated / Promoted / 2nd Division
    "Darmstadt 98": "Darmstadt 98",
    "SV Darmstadt 98": "Darmstadt 98",
    "FC St. Pauli": "St. Pauli",
    "St. Pauli": "St. Pauli",
    "Holstein Kiel": "Holstein Kiel",
    "Kieler SV Holstein": "Holstein Kiel",
    "1. FC Koln": "FC Koln",
    "FC Koln": "FC Koln",
    "Koln": "FC Koln",
    "Cologne": "FC Koln",
    "Hertha BSC": "Hertha BSC",
    "Hertha Berlin": "Hertha BSC",
    "Schalke 04": "Schalke 04",
    "FC Schalke 04": "Schalke 04",
    "Fortuna Dusseldorf": "Dusseldorf",
    "Greuther Furth": "Greuther Furth",
    "Arminia Bielefeld": "Arminia",
    "Hansa Rostock": "Rostock"
}