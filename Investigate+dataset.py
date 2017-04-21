
# coding: utf-8

# In[34]:

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

OSM_PATH = "miami.osm"

LOWER_COLON = re.compile(r'^([a-zA-Z]|_)+:([a-zA-Z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

node_tags_sets = {}
ways_tags_sets = {}
way_tags_set = set()

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []
    position_way = 0
    # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        
        node_attribs['id'] = element.attrib['id']
        node_attribs['user'] = element.attrib['user']
        node_attribs['uid'] = element.attrib['uid']
        node_attribs['version'] = element.attrib['version']
        node_attribs['lat'] = element.attrib['lat']
        node_attribs['lon'] = element.attrib['lon']
        node_attribs['timestamp'] = element.attrib['timestamp']
        node_attribs['changeset'] = element.attrib['changeset']
        
        for child in element:
            tag_dict = {}
            
            if 'k' in child.attrib and not re.search(PROBLEMCHARS, child.attrib['k']):
                tag_dict['id'] = node_attribs['id']
                
                if re.search(LOWER_COLON, child.attrib['k']):
                    type_match = re.match("([a-zA-Z0-9_?]*):", child.attrib['k'])
                    type_str = type_match.group(1)
                    tag_dict['type'] = type_str
                    type_str = type_str + ':'
                    key = child.attrib['k'].replace(type_str,'')
                    tag_dict['key'] = key
                else:
                    tag_dict['key'] = child.attrib['k']
                    tag_dict['type'] = 'regular'
                
                tag_dict['value'] = child.attrib['v']
                tags.append(tag_dict)
                
                if tag_dict['type'] == 'regular' and tag_dict['key'] not in node_tags_sets.keys():
                    node_tags_sets[tag_dict['key']] = set()       
                
                if tag_dict['type'] == 'regular':
                    node_tags_sets[tag_dict['key']].add(tag_dict['value'])
            
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        
        way_attribs['id'] = element.attrib['id']
        way_attribs['user'] = element.attrib['user']
        way_attribs['uid'] = element.attrib['uid']
        way_attribs['version'] = element.attrib['version']
        way_attribs['timestamp'] = element.attrib['timestamp']
        way_attribs['changeset'] = element.attrib['changeset']
        
        for child in element:
            tag_dict = {}
            postcode_dict = {}
            
            if 'k' in child.attrib:
                tag_dict = {}
                tag_dict['id'] = way_attribs['id']
                
                if re.search(LOWER_COLON, child.attrib['k']):
                    type_match = re.match("([a-zA-Z0-9_?]*):", child.attrib['k'])
                    type_str = type_match.group(1)
                    tag_dict['type'] = type_str
                    type_str = type_str + ':'
                    key = child.attrib['k'].replace(type_str,'')
                    tag_dict['key'] = key
                else:
                    tag_dict['key'] = child.attrib['k']
                    tag_dict['type'] = 'regular'
                
                tag_dict['value'] = child.attrib['v']
                
                way_tags_set.add(tag_dict["key"])
                    
                tags.append(tag_dict)
                
# ================================================== #
#uncomment one of the functions below to investigate #
# ================================================== #

                #investigating street abbreviations
                '''if tag_dict['key'] == 'street' and tag_dict['type'] == 'addr':
                    tag_dict['value'] = update_name(tag_dict['value'], mapping)
                    last_word = tag_dict['value'].rsplit(None, 1)[-1]

                    if last_word not in ways_tags_sets.keys():
                        ways_tags_sets[last_word] = set()    

                    ways_tags_sets[last_word].add(tag_dict['value'])'''
                
                #investigating state names
                '''
                if tag_dict['key'] == 'state':

                    if tag_dict['value'] not in ways_tags_sets.keys():
                        ways_tags_sets[tag_dict['value']] = 0     

                    #print tag_dict['value']
                    ways_tags_sets[tag_dict['value']] = ways_tags_sets[tag_dict['value']] + 1'''
                
                #investigating postcodes
                '''if tag_dict['key'] == 'postcode':
                    tag_dict['value'] = fix_postcode(tag_dict['value'])
                    
                    if isinstance(tag_dict['value'], list):
                        try:
                            postcode_dict['value'] = int(tag_dict['value'][1])
                            postcode_dict['id'] = tag_dict['id']
                            postcode_dict['value'] = tag_dict['value'][1]
                            postcode_dict['key'] = 'addition'
                            postcode_dict['type'] = 'postcode'
                            tags.append(postcode_dict)
                        except ValueError:
                            #Handle the exception
                            pass
                        
                        tag_dict['value'] = tag_dict['value'][0]
                        print postcode_dict

                    if tag_dict['value'] not in ways_tags_sets.keys():
                        ways_tags_sets[tag_dict['value']] = 0    

                    #print tag_dict['value']
                    ways_tags_sets[tag_dict['value']] = ways_tags_sets[tag_dict['value']] + 1'''
                
                #investigating keys in general        
                '''if tag_dict['key'] not in ways_tags_sets.keys():
                    ways_tags_sets[tag_dict['key']] = set()       
                
                ways_tags_sets[tag_dict['key']].add(tag_dict['value'])'''
                    
                
            elif 'nd' in child.tag:
                way_dict = {}
                way_dict['id'] = way_attribs['id']
                way_dict['node_id'] = child.attrib['ref']
                way_dict['position'] = position_way
                position_way += 1
                way_nodes.append(way_dict)
            else:
                print "Else"
                print child.attrib
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in):
    """Iteratively process each XML element and write to csv(s)"""
        

    for element in get_element(file_in, tags=('node', 'way')):
        el = shape_element(element)


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH)
    
    #print sorted(way_tags_set)
    
    #printing table of sets for way_tags and node_tags in order to determine data quality and possible errors
    #pprint.pprint(ways_tags_sets, width=12)
    #pprint.pprint(node_tags_sets, width=12)


# In[ ]:



