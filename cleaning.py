#
def update_name(name, mapping, street_type_re):
    """function updates the street abbreviation to a regular street name
    
    Args:
        name(str): name of the street which name should be updated
        mapping(dict): mapping of names abbreviations
        street_type_re(compiled regular expression): regular expression extracting street type


    Returns:
        str: new street name"""

    result = street_type_re.search(name)
    street_type = result.group()
    
    if street_type in mapping.keys():
        new_street_type = mapping[street_type]
        replaced_name = name.replace(street_type, new_street_type)
    else:
        replaced_name = name

    return replaced_name

def fix_postcode (postcode):
    """function which fixes postcodes either they begin with FL or have two parts
    
    Args:
        postcode(str): every postcode in string format


    Returns:
        str: new postcode if postcode doesn't contain hyphen
        [str, str]: new postcodes if postcode contains hypen"""

    if postcode.startswith('FL'):
        postcode = postcode[3:]
    
    if '-' in postcode:
        postcode = postcode.split('-')
    
    return postcode
