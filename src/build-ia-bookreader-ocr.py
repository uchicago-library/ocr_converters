from PIL import Image
import requests
import xml.etree.ElementTree as ElementTree

class OCRBuilder():
    def __init__(self, file_dict, min_year, max_year):
        if not all([k in file_dict for k in ('dc', 'jpgs', 'ocr_files', 'tifs', 'txt')]):
            raise KeyError
        self.file_dict = file_dict
       
        self.min_year = min_year 
        self.max_year = max_year

        self.dc = ElementTree.fromstring(requests.get(self.file_dict['dc']).text)
        
    def get_jpg_size(self, i):
        return Image.open(requests.get(self.file_dict['jpgs'][i], stream=True).raw).size

    def get_tif_size(self, i):
        return Image.open(requests.get(self.file_dict['tifs'][i], stream=True).raw).size

    def get_jpg_tif_ratio(self, i):
        return float(self.get_jpg_size(i)[1]) / float(self.get_tif_size(i)[1])
    
    def get_dc_date(self):
        return self.dc.find('date').text

    def get_dc_description(self):
        return self.dc.find('description').text

    def get_dc_identifier(self):
        return self.dc.find('identifier').text
        
    def get_dc_title(self):
        return self.dc.find('title').text

    def get_decade(self):
        return "%s0's" % self.get_year()[0:3]

    def get_publication_type(self):
        return 'student' if self.get_dc_title() in ('Cap and Gown', 'Daily Maroon') else 'university'

    def get_volume_number(self):
        return int(self.get_dc_identifier().split('-')[2].lstrip('0'))

    def get_year(self):
        return self.get_dc_date().split('-')[0]

    def get_year_range(self):
        return '%s-%s' % (self.min_year, self.max_year)

    def get_metadata_node(self):
        ElementTree.register_namespace('http://cdlib.org/xtf','xtf')
    
        xtf_converted_book = ElementTree.Element('xtf-converted-book')
        meta = ElementTree.SubElement(xtf_converted_book, 'xtf:meta')
        ElementTree.SubElement(meta, 'facet-sidebartitle', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'yes',
            'xtf:tokenize': 'no'
        }).text = '%s::Volume %02d' % (self.get_dc_title(), self.get_volume_number())

        ElementTree.SubElement(meta, 'facet-title', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'yes',
            'xtf:tokenize': 'no'
        }).text = '%s::Volume %02d' % (self.get_dc_title(), self.get_volume_number())

        ElementTree.SubElement(meta, 'browse-title', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'yes'
        }).text = '%s Volume %02d' % (self.get_dc_title(), self.get_volume_number())

        ElementTree.SubElement(meta, 'facet-date', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'yes',
            'xtf:tokenize': 'no'
        }).text = '%s::%s' % (self.get_decade(), self.get_year())

        ElementTree.SubElement(meta, 'browse-date', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'yes'
        }).text = '%s %s' % (self.get_decade(), self.get_year())

        ElementTree.SubElement(meta, 'range-date', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'no'
        }).text = self.get_year()

        ElementTree.SubElement(meta, 'facet-category', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'yes',
            'xtf:tokenize': 'no'
        }).text = '%s::%s' % (self.get_publication_type(), self.get_dc_title())

        ElementTree.SubElement(meta, 'browse-category', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'yes'
        }).text = self.get_publication_type()

        ElementTree.SubElement(meta, 'sort-identifier', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'no'
        }).text = self.get_dc_identifier()

        ElementTree.SubElement(meta, 'display-title', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'no'
        }).text = '%s (%s)' % (self.get_dc_title(), self.get_year_range())

        ElementTree.SubElement(meta, 'display-item', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'no'
        }).text = 'Volume %s (%s)' % (self.get_volume_number(), self.get_year())

        ElementTree.SubElement(meta, 'browse-description', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'yes'
        }).text = self.get_dc_description()

        ElementTree.SubElement(meta, 'year', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'no'
        }).text = self.get_year()

        ElementTree.SubElement(meta, 'facet-volume', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'no',
            'xtf:tokenize': 'no'
        }).text = str(self.get_volume_number())

        return meta

    # in PHP I used mb_convert_encoding($fields[4], "UTF-8", "ISO-8859-1") on 'text'
    def get_position_data_from_pos(self, data_str, scale):
        output = []
        for line in data_str.split('\n'):
            fields = line.split('\t')
            output.append({
                'x': int(float(fields[0]) * scale),
                'y': int(float(fields[1]) * scale),
                'w': int(float(fields[2]) * scale),
                'h': int(float(fields[3]) * scale),
                'text': fields[4]
            })
        return output

    # in PHP I used mb_convert_encoding($fields[4], "UTF-8", "ISO-8859-1") on 'text'
    def get_position_data_from_alto(self, xml, scale):
        ElementTree.registerNamespace('a', 'http://www.loc.gov/standards/alto/ns-v2#')
        fields = []
        for string in xml.findall('a:string'):
            fields.append({
                'x': int(float(string.get('HPOS')) * scale),
                'y': int(float(string.get('VPOS')) * scale),
                'w': int(float(string.get('WIDTH')) * scale),
                'h': int(float(string.get('HEIGHT')) * scale),
                'text': string.get('CONTENT')
            })
        return fields
    
    def get_position_data(self, i):
        scale = self.get_jpg_tif_ratio(i)
        data_str = requests.get(self.ocr_files[i]).text
        try:
            xml = ElementTree.fromstring(data_str)
        except ParseError:
            return self.get_position_data_from_pos(data_str, scale)

        return self.get_position_data_from_alto(xml, scale)

    def get_structural_dict(self):
        data_str = requests.get(self.data_files['txt']).text
        output = {}
        for line in data_str.explode('\n'):
            fields = line.explode('\t')
            output[fields[0]] = fields[1]
        return output 

    #
    # The words are associative arrays with x, y, w, and h parameters.
    # Check to see if there should be a newline between them. 
    #
    def newline_between_words(self, word1, word2):
        # If word2 is to the left of word1, there should 
        # be a newline between these words.
        if word2['x'] < (word1['x'] + word1['w']):
            return True

        # If every part of word2 is above word1, there
        # should be a newline between them. 
        if word2['y'] + (word2['h'] < word1['y']):
            return True;

        # If every part of word2 is below word1, there
        # should be a newline between them.
        if word2['y'] > (word1['y'] + word1['h']):
            return True;

        return False;

    def pos_data_line_groups(self, i):
        pos_data = self.get_position_data(i)

        lines = []
        line = []
        while True:
            # When posData is empty we're done.
            if len(pos_data) == 0:
                # If there is a line to add, add it.
                if len(line) > 0:
                    lines.append(line)
                break

            # If the current line is empty, get an element from pos_data.
            if len(line) == 0:
                line.append(pos_data.pop(0))
                continue

            # If the next word is on the same line as the previous word... */ 
            if not self.newline_between_words(line[-1], pos_data[0]):
                line.append(pos_data.pop(0))
            else:
                lines.append(line)
                line = []
        return lines

    def leaf_data_from_pos_data(self, i):
        pos_data_line_groups = self.pos_data_line_groups(i)

        records = []
        for pos_data_lines in pos_data_line_groups:
            rs = []
            bs = []
            for pos_data_line in pos_data_lines:
                rs.append(pos_data_line['x'] + pos_data_line['w'])
                bs.append(pos_data_line['y'] + pos_data_line['h'])

            records.append({
                't': min([line['y'] for line in pos_data_lines]),
                'b': max(bs),
                'l': min([line['x'] for line in pos_data_lines]),
                'r': max(rs),
                'words': self.line_data_from_pos_data(pos_data_lines)
            })
        return records

    def line_data_from_pos_data(self, pos_data_lines):
        words = []
        for pos_data_line in pos_data_lines:
            words.append({
                'l': pos_data_line['x'],
                'r': pos_data_line['x'] + pos_data_line['w'],
                't': pos_data_line['y'],
                'b': pos_data_line['y'] + pos_data_line['h'],
                'text': pos_data_line['text']
            })
        return words

    def scale_leaf_data(self, leaf_data, scale):
        l = 0
        while l < len(leaf_data):
            for k in ('l', 't', 'r', 'b'):
                leaf_data[l][k] = (int)(leaf_data[l][k] * scale)
            w = 0
            while w < len(leaf_data[l]['words']):
                for k in ('l', 't', 'r', 'b'):
                    leaf_data[l]['words'][w][k] = (int)(leaf_data[l]['words'][w][k] * scale)
                w = w + 1
            l = l + 1
        return leaf_data

    def get_line_spacing(self, leaf_data, l):
        spacing = []
    
        w = 0   
        while w < len(leaf_data[l]['words']):
            word_width = leaf_data[l]['words'][w]['r'] - leaf_data[l]['words'][w]['l']
            spacing.append(word_width)
    
            if w < len(leaf_data[l]['words']) - 1:
                space_width = leaf_data[l]['words'][w + 1]['l'] - leaf_data[l]['words'][w]['r']
                spacing.append(space_width)
            w = w + 1
        return spacing

    def get_spacing_coords(self, spacing, w):
        offset_l = 0
        s = 0
        while s < w * 2:
            offset_l = offset_l + spacing[s]
            s = s + 1
    
        offset_r = 0
        s = 0
        while s <= w * 2:
            offset_r = offset_r + spacing[s]
            s = s + 1
    
        return (offset_l, offset_r)

    def get_line_text(self, line):
        if 'words' in line:
            return ' '.join([word['text'] for word in line['word']])
        else:
            return ''

    def spacing_to_string(self, spacing):
        return ' '.join([str(space) for space in spacing])

    # leaf_num is an eight digit string, like '00000001'
    def build_xml_leaf(self, leaf_data, leaf_num, human_readable_leaf_num):
        '''
        JUST AN EXAMPLE FROM ABOVE...
        ElementTree.SubElement(meta, 'facet-sidebartitle', attrib={
            'xtf:meta': 'true',
            'xtf:facet': 'yes',
            'xtf:tokenize': 'no'
        }).text = '%s::Volume %02d' % (self.get_dc_title(), self.get_volume_number())
        '''

        jpg_size = self.get_jpg_size(int(leaf_num))
    
        leaf = ElementTree.Element('leaf', attrib={
            'leafNum': leaf_num.lstrip('0'),
            'type': '',
            'access': 'true',
            'imgFile': '%s.jpg' % leaf_num,
            'x': jpg_size[0],
            'y': jpg_size[1],
            'humanReadableLeafNum': human_readable_leaf_num,
            'xtf:sectionType': leaf_num
        })
   
        # need namespace: xtf = http://cdlib.org/xtf
   
        ElementTree.SubElement(leaf, 'cropBox', attrib={ 
            'x': jpg_size[0],
            'y': jpg_size[1],
            'w': jpg_size[0],
            'h': jpg_size[1]
        })
    
        l = 0
        for line in leaf_data:
            line_element = ElementTree.SubElement(leaf, 'line', attrib={
                'l': line['l'],
                't': line['t'],
                'r': line['r'],
                'b': line['b'],
                'spacing': spacingToString(line['spacing'])
            }).text = self.get_line_text(self, line)
            l = l + 1
        return leaf

    def build_xml(self):
        structural_dict = o.get_structural_dict
        #JEJ
        for leaf_num in range(len(o['ocr_files'])):
            leaf_data = o.leaf_data_from_pos_data(leaf_num)

            leaf_data = o.scale_leaf_data(leaf_data, o.get_scale(i))

            # Add line spacing info to each line. This has to happen after scaling.
            i = 0
            while i < len(leaf_data):
                leaf_data[i]['spacing'] = o.get_line_spacing(leaf_data, i)
                i = i + 1

#
# MAIN 
#

o = OCRBuilder({
    'dc': 'http://campub-xtf.lib.uchicago.edu/xtf/data/bookreader/mvol-0005-0001-0001/mvol-0005-0001-0001.dc.xml',
    'jpgs': [
        'http://campub-xtf.lib.uchicago.edu/xtf/data/bookreader/mvol-0005-0001-0001/00000001.jpg'
    ],
    'ocr_files': [
        'http://campub-xtf.lib.uchicago.edu/xtf/data/bookreader/mvol-0005-0001-0001/00000001.jpg'
    ],
    'tifs': [
        'http://campub-xtf.lib.uchicago.edu/xtf/data/bookreader/mvol-0005-0001-0001/00000001.jpg'
    ],
    'txt': 'http://campub-xtf.lib.uchicago.edu/xtf/data/bookreader/mvol-0005-0001-0001/mvol-0005-0001-0001.txt',
}, 1900, 2000)




