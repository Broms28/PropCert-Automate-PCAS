import re

def address_sort_key(address):
    """
    Parses an address to return a tuple (street_name, street_number)
    for smart sorting. E.g. '88 Hornsey Lane' -> ('hornsey lane', 88)
    """
    if not address:
        return ("", 0)
    address = address.strip()
    match = re.match(r'^(\d+)\s+(.*)', address)
    if match:
        num = int(match.group(1))
        street = match.group(2).lower()
        return (street, num)
    return (address.lower(), 0)

def property_sort_key(prop):
    return address_sort_key(prop.address)

def flat_sort_key(flat):
    if not flat or not flat.name:
        return ("", 0)
    return address_sort_key(flat.name)

def tenant_sort_key(tenant):
    if hasattr(tenant, 'property') and tenant.property:
        prop = tenant.property
    elif hasattr(tenant, 'flat') and tenant.flat and hasattr(tenant.flat, 'property'):
        prop = tenant.flat.property
    else:
        prop = None
        
    prop_key = property_sort_key(prop) if prop else ("", 0)
    flat_key = flat_sort_key(tenant.flat) if hasattr(tenant, 'flat') and tenant.flat else ("", 0)
    return (prop_key[0], prop_key[1], flat_key[0], flat_key[1])
