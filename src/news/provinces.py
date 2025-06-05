PROVINCES = {
    "Alberta": {
        "name": "Alberta",
        "abbr": "AB",
        "cities": ["Edmonton", "Calgary", "Red Deer", "Lethbridge", "Fort McMurray", "Medicine Hat", "Grande Prairie"],
        "regions": ["Southern Alberta", "Northern Alberta", "Central Alberta", "Rocky Mountains", "Badlands"],
        "search_terms": ["Alberta news", "Calgary news", "Edmonton news", "Alberta Canada"]
    },
    "British Columbia": {
        "name": "British Columbia",
        "abbr": "BC",
        "cities": ["Vancouver", "Victoria", "Kelowna", "Kamloops", "Prince George", "Nanaimo", "Abbotsford"],
        "regions": ["Lower Mainland", "Vancouver Island", "Interior BC", "Northern BC", "Sunshine Coast"],
        "search_terms": ["BC news", "British Columbia news", "Vancouver news", "Victoria BC news"]
    },
    "Manitoba": {
        "name": "Manitoba",
        "abbr": "MB",
        "cities": ["Winnipeg", "Brandon", "Steinbach", "Thompson", "Portage la Prairie", "Selkirk"],
        "regions": ["Winnipeg Capital Region", "Western Manitoba", "Northern Manitoba", "Eastern Manitoba"],
        "search_terms": ["Manitoba news", "Winnipeg news", "Manitoba Canada news"]
    },
    "New Brunswick": {
        "name": "New Brunswick",
        "abbr": "NB",
        "cities": ["Fredericton", "Saint John", "Moncton", "Dieppe", "Miramichi", "Bathurst"],
        "regions": ["Greater Moncton", "Greater Saint John", "Fredericton Region", "Northern NB"],
        "search_terms": ["New Brunswick news", "NB news", "Moncton news", "Saint John news"]
    },
    "Newfoundland and Labrador": {
        "name": "Newfoundland and Labrador",
        "abbr": "NL",
        "cities": ["St. John's", "Mount Pearl", "Corner Brook", "Conception Bay South", "Grand Falls-Windsor"],
        "regions": ["Avalon Peninsula", "Central Newfoundland", "Western Newfoundland", "Labrador"],
        "search_terms": ["Newfoundland news", "NL news", "St Johns news", "Newfoundland and Labrador"]
    },
    "Northwest Territories": {
        "name": "Northwest Territories",
        "abbr": "NT",
        "cities": ["Yellowknife", "Hay River", "Inuvik", "Fort Smith", "Behchokǫ̀"],
        "regions": ["North Slave", "South Slave", "Dehcho", "Sahtu", "Beaufort Delta"],
        "search_terms": ["Northwest Territories news", "NWT news", "Yellowknife news", "Arctic news"]
    },
    "Nova Scotia": {
        "name": "Nova Scotia",
        "abbr": "NS",
        "cities": ["Halifax", "Dartmouth", "Sydney", "Truro", "New Glasgow", "Glace Bay"],
        "regions": ["Halifax Regional Municipality", "Cape Breton", "South Shore", "Annapolis Valley"],
        "search_terms": ["Nova Scotia news", "Halifax news", "Cape Breton news", "NS news"]
    },
    "Nunavut": {
        "name": "Nunavut",
        "abbr": "NU",
        "cities": ["Iqaluit", "Rankin Inlet", "Arviat", "Baker Lake", "Cambridge Bay"],
        "regions": ["Qikiqtaaluk", "Kivalliq", "Kitikmeot"],
        "search_terms": ["Nunavut news", "Iqaluit news", "Arctic Canada news", "Nunavut territory"]
    },
    "Ontario": {
        "name": "Ontario",
        "abbr": "ON",
        "cities": ["Toronto", "Ottawa", "Mississauga", "Hamilton", "London", "Kitchener", "Windsor"],
        "regions": ["Greater Toronto Area", "Ottawa Valley", "Southwestern Ontario", "Northern Ontario"],
        "search_terms": ["Ontario news", "Toronto news", "Ottawa news", "GTA news"]
    },
    "Prince Edward Island": {
        "name": "Prince Edward Island",
        "abbr": "PE",
        "cities": ["Charlottetown", "Summerside", "Stratford", "Cornwall", "Montague"],
        "regions": ["Queens County", "Prince County", "Kings County"],
        "search_terms": ["PEI news", "Prince Edward Island news", "Charlottetown news", "Island news"]
    },
    "Quebec": {
        "name": "Quebec",
        "abbr": "QC",
        "cities": ["Montreal", "Quebec City", "Laval", "Gatineau", "Longueuil", "Sherbrooke"],
        "regions": ["Greater Montreal", "Quebec City Region", "Eastern Townships", "Laurentides"],
        "search_terms": ["Quebec news", "Montreal news", "Quebec City news", "Quebec Canada"]
    },
    "Saskatchewan": {
        "name": "Saskatchewan",
        "abbr": "SK",
        "cities": ["Saskatoon", "Regina", "Prince Albert", "Moose Jaw", "Swift Current"],
        "regions": ["Southern Saskatchewan", "Central Saskatchewan", "Northern Saskatchewan"],
        "search_terms": ["Saskatchewan news", "Regina news", "Saskatoon news", "Sask news"]
    },
    "Yukon": {
        "name": "Yukon",
        "abbr": "YT",
        "cities": ["Whitehorse", "Dawson City", "Watson Lake", "Haines Junction", "Carmacks"],
        "regions": ["Southern Yukon", "Central Yukon", "Northern Yukon"],
        "search_terms": ["Yukon news", "Whitehorse news", "Yukon territory news", "Northern Canada news"]
    }
}

def get_province_info(province_name: str) -> dict:
    """Get province information by name (case-insensitive)"""
    for key, value in PROVINCES.items():
        if key.lower() == province_name.lower():
            return value
    return None

def get_all_provinces() -> list:
    """Get list of all provinces with their info"""
    return list(PROVINCES.values())