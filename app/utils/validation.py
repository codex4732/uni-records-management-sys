from flask import abort


def validate_id(*ids):
    for id in ids:
        if not str(id).isdigit():
            abort(400, description="Invalid ID format - must be numeric")
