import hashlib


def short_sha(value, digits=8):
    """Calculate a short sha from an input string, with a certain degree of uniqueness"""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:digits]
