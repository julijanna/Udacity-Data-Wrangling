
# coding: utf-8

# In[24]:

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cleaning

OSM_PATH = "miami_florida.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-zA-Z]|_)+:([a-zA-Z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Mapping of street types
mapping = {"St": "Street",
           "St.": "Street",
           "Rd" : "Road",
           "Ave" : "Avenue",
           "AVE" : "Avenue",
           "Blvd" : "Boulevard",
           "Blvd." : "Boulevard",
           "Cir" : "Circle",
           "Ct" : "Court",
           "Dr" : "Drive",
           "HWY" : "Highway",
           "N" : "North",
           "Pkwy" : "Parkway",
           "Trl" : "Trail",
           "road" : "Road",
           "street" : "Street"
            }

#function which prepares every XML Tree element to have a csv-friendly structure
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []
    position_way = 0
    
    # Handle secondary tags the same way for both node and way elements
    # Handling node tags
    if element.tag == 'node':
        
        #handling nodes
        node_attribs['id'] = element.attrib['id']
        node_attribs['user'] = element.attrib['user']
        node_attribs['uid'] = element.attrib['uid']
        node_attribs['version'] = element.attrib['version']
        node_attribs['lat'] = element.attrib['lat']
        node_attribs['lon'] = element.attrib['lon']
        node_attribs['timestamp'] = element.attrib['timestamp']
        node_attribs['changeset'] = element.attrib['changeset']
        
        for child in element:
            #handling k tags
            if 'k' in child.attrib and not re.search(PROBLEMCHARS, child.attrib['k']):
                tag_dict = {}
                tag_dict['id'] = node_attribs['id']
                
                #checking if ':' is in tag if yes, extracting first part as a type and rest as key
                if re.search(LOWER_COLON, child.attrib['k']):
                    type_match = re.match("([a-zA-Z0-9_?]*):", child.attrib['k'])
                    type_str = type_match.group(1)
                    tag_dict['type'] = type_str
                    type_str = type_str + ':'
                    key = child.attrib['k'].replace(type_str,'')
                    tag_dict['key'] = key
                    
                #if there is no ':' in tag then type: regular
                else:
                    tag_dict['key'] = child.attrib['k']
                    tag_dict['type'] = 'regular'
                
                tag_dict['value'] = child.attrib['v']
                tags.append(tag_dict)
            
        return {'node': node_attribs, 'node_tags': tags}
    
    #Handling way tags
    elif element.tag == 'way':
        
        #handling ways
        way_attribs['id'] = element.attrib['id']
        way_attribs['user'] = element.attrib['user']
        way_attribs['uid'] = element.attrib['uid']
        way_attribs['version'] = element.attrib['version']
        way_attribs['timestamp'] = element.attrib['timestamp']
        way_attribs['changeset'] = element.attrib['changeset']
        
        for child in element:
            tag_dict = {}
            postcode_dict = {}
            
            #handling k tags
            if 'k' in child.attrib:
                tag_dict = {}
                tag_dict['id'] = way_attribs['id']
                
                #checking if ':' is in tag if yes, extracting first part as a type and rest as key
                if re.search(LOWER_COLON, child.attrib['k']):
                    type_match = re.match("([a-zA-Z0-9_?]*):", child.attrib['k'])
                    type_str = type_match.group(1)
                    tag_dict['type'] = type_str
                    type_str = type_str + ':'
                    key = child.attrib['k'].replace(type_str,'')
                    tag_dict['key'] = key
                    
                #if there is no ':' in tag then type: regular
                else:
                    tag_dict['key'] = child.attrib['k']
                    tag_dict['type'] = 'regular'
                
                tag_dict['value'] = child.attrib['v']
                
                #correcting street names
                if tag_dict['key'] == 'street' and tag_dict['type'] == 'addr':
                    tag_dict['value'] = cleaning.update_name(tag_dict['value'], mapping, street_type_re)
                    
                #correcting postcodes
                if tag_dict['key'] == 'postcode':
                    tag_dict['value'] = cleaning.fix_postcode(tag_dict['value'])
                    
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
                        
                        try:
                            tag_dict['value'] = int(tag_dict['value'][0])
                        except ValueError:
                            tag_dict = {}
                            print "Poscode not convertable to int"
                            
                #correcting state names            
                if tag_dict['key'] == 'state' and (tag_dict['value'].startswith('F') or tag_dict['value'].startswith('f')) and tag_dict['value'] != 'FL':
                    tag_dict['value'] = 'FL'
                    
                    
                tags.append(tag_dict)              
                
            elif 'nd' in child.tag:
                way_dict = {}
                way_dict['id'] = way_attribs['id']
                way_dict['node_id'] = child.attrib['ref']
                way_dict['position'] = position_way
                position_way += 1
                way_nodes.append(way_dict)
                

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


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,         codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:
        
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH)


# In[ ]:



