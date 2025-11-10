from typing import Optional

# Minimal list of common Google News topic IDs.
# You can pass either a friendly name (key) or the full hashed ID as seen in Google News URLs.
TOPIC_MAP = {
    # Friendly names
    "top_stories": "CAAqIggKIhxDQkFTRHdvSkwyMHZNREZpYjJvU0FtVnVLQUFQAQ",
    "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRVXlnQVAB",
    "nation": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRVkNnQVAB",
    "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRV1dnQVAB",
    "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRV2dnQVAB",
    "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRV3FnQVAB",
    "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRV2tnQVAB",
    "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRVmdnQVAB",
    "health": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRVmtnQVAB",
    # Aliases
    "tech": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pRV2dnQVAB",
}

def resolve_topic_id(value: str) -> str:
    """
    If a friendly name is provided, map to ID. Otherwise assume 'value' is already a topic hash.
    """
    if not value:
        raise ValueError("Topic not specified")
    v = value.strip().lower()
    return TOPIC_MAP.get(v, value)