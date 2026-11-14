"""Учебный дефект границы бесплатной доставки."""
def shipping(total):
    return 0 if total > 5000 else 500
