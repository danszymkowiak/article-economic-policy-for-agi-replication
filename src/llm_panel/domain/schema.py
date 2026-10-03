"""The JSON schema every model response is validated against (score 0-100 plus rationale)."""

RESPONSE_SCHEMA: dict = {
    "type": "object",
    "required": ["ratings"],
    "additionalProperties": False,
    "properties": {
        "ratings": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["policy", "score", "rationale"],
                "additionalProperties": False,
                "properties": {
                    "policy": {"type": "string", "minLength": 1},
                    "score": {"type": "number", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "string", "maxLength": 1000},
                },
            },
        }
    },
}
