"""The JSON schemas model responses are validated against (score 0-100 plus rationale).

RESPONSE_SCHEMA keys each entry by policy label (D1 joint scoring, smoketests).
CRITERION_RESPONSE_SCHEMA keys each entry by criterion id: the study's persona x policy call
returns one policy's profile over every criterion, as in the paper's Appendix B profiles.
"""


def _ratings_schema(key: str) -> dict:
    return {
        "type": "object",
        "required": ["ratings"],
        "additionalProperties": False,
        "properties": {
            "ratings": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [key, "score", "rationale"],
                    "additionalProperties": False,
                    "properties": {
                        key: {"type": "string", "minLength": 1},
                        "score": {"type": "number", "minimum": 0, "maximum": 100},
                        "rationale": {"type": "string", "maxLength": 1000},
                    },
                },
            }
        },
    }


RESPONSE_SCHEMA: dict = _ratings_schema("policy")
CRITERION_RESPONSE_SCHEMA: dict = _ratings_schema("criterion")
