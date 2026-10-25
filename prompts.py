
from pathlib import Path
from config import ALLOWED

PROMPT_FILE = Path(__file__).parent / "prompts" / "sap_commands.txt"


def load_prompt():
    return PROMPT_FILE.read_text(encoding="utf-8")

def load_md04_prompt():
    prompt_file = Path(__file__).parent / "prompts" / "md04_answer.txt"
    return prompt_file.read_text(encoding="utf-8")

# RESPONSE_SCHEMA = {
#     "type": "object",
#     "properties": {
#         "tcode": {
#             "type": "string",
#             "enum": list(ALLOWED.keys()) + ["NONE"]
#         }
#     },
#     "required": ["tcode"],
#     "additionalProperties": False
# }


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "tcode": {
            "type": "string",
            "enum": list(ALLOWED.keys()) + ["NONE"]
        },
        "material": {
            "type": ["string", "null"]
        },
        "plant": {
            "type": ["string", "null"]
        },
        "period": {
            "type": ["string", "null"],
            "enum": [
                "next_7_days",
                "next_week",
                "this_month",
                "next_month",
                "all",
                None
            ]
        }
    },
    "required": ["tcode", "material", "plant", "period"],
    "additionalProperties": False
}

