#!/usr/bin/env python3

"""Usage:
   build_ia_bookreader_ocr --local-root=<path> <identifier> <min-year> <max-year>
"""

import os, sys
import xml.etree.ElementTree as ElementTree
from PIL import Image
from docopt import docopt

def list_mvol_files(local_root, identifier, subdir):
    '''Get a list of complete paths to mvol files in ALTO, JPEG, POS or TIFF
       directories
    '''
    subdir_path = '{}{}{}{}{}'.format(
        local_root,
        os.sep,
        identifier.replace('-', os.sep),
        os.sep,
        subdir
    )
    files = []
    for f in os.listdir(subdir_path):
        files.append('{}{}{}'.format(subdir_path, os.sep, f))
    return sorted(files)

class OCRBuilder():
    def __init__(self, file_dict, min_year, max_year):
        if not all([k in file_dict for k in ('dc', 'jpgs', 'ocr_files', 'tifs', 'txt')]):
            raise KeyError
        self.file_dict = file_dict
       
        self.min_year = min_year 
        self.max_year = max_year

        self.dc = ElementTree.fromstring(open(self.file_dict['dc']).read())

        ElementTree.register_namespace('xtf', 'http://cdlib.org/xtf')
        
    def get_jpg_size(self, i):
        ''' Get the size of a jpeg from the self.file_dict['jpgs'] list.
        '''
        return Image.open(self.file_dict['jpgs'][i]).size

    def get_tif_size(self, i):
        ''' Get the size of a tiff from the self.file_dict['tifs'] list.
        '''
        return Image.open(self.file_dict['tifs'][i]).size

    def get_jpg_tif_ratio(self, i):
        ''' Get the amount that jpegs "shrunk" compared to tiffs, so we
            can rescale OCR data.
        '''
        return float(self.get_jpg_size(i)[1]) / float(self.get_tif_size(i)[1])
    
    def get_decade(self):
        return "%s0s" % self.get_year()[0:3]

    def get_publication_type(self):
        return 'student' if self.dc.find('title').text in ('Cap and Gown', 'Daily Maroon') else 'university'

    def get_volume_number(self):
        return int(self.dc.find('identifier').text.split('-')[2].lstrip('0'))

    def get_year(self):
        ''' Get the year from a date string embedded in DC data- e.g.
            2020-04-22 to 2020.
        '''
        return self.dc.find('date').text.split('-')[0]

    def get_human_readable_date(self):
        months = {
            '01': 'January',
            '02': 'February',
            '03': 'March',
            '04': 'April',
            '05': 'May',
            '06': 'June',
            '07': 'July',
            '08': 'August',
            '09': 'September',
            '10': 'October',
            '11': 'November',
            '12': 'December'
        }
        d = self.dc.find('date').text.split('-')
        if len(d) == 1: # year
            return d[0]
        elif len(d) == 2: # month  year
            return '%s %s' % (months[d[1]], d[0])
        else:
            return '%s %d, %s' % (months[d[1]], int(d[2]), d[0])

    def get_meta(self):
        meta = ElementTree.Element('{http://cdlib.org/xtf}meta')
        ElementTree.SubElement(meta, 'facet-sidebartitle', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'yes',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = '%s::Volume %02d' % (self.dc.find('title').text, self.get_volume_number())

        ElementTree.SubElement(meta, 'facet-title', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'yes',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = '%s::Volume %02d' % (self.dc.find('title').text, self.get_volume_number())

        ElementTree.SubElement(meta, 'browse-title', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'yes'
        }).text = '%s Volume %02d' % (self.dc.find('title').text, self.get_volume_number())

        ElementTree.SubElement(meta, 'facet-date', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'yes',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = '%s::%s' % (self.get_decade(), self.get_year())

        ElementTree.SubElement(meta, 'browse-date', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'yes'
        }).text = '%s %s' % (self.get_decade(), self.get_year())

        ElementTree.SubElement(meta, 'range-date', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = self.get_year()

        ElementTree.SubElement(meta, 'facet-category', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'yes',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = '%s::%s' % (self.get_publication_type(), self.dc.find('title').text)

        ElementTree.SubElement(meta, 'browse-category', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'yes'
        }).text = self.get_publication_type()

        ElementTree.SubElement(meta, 'sort-identifier', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = self.dc.find('identifier').text

        ElementTree.SubElement(meta, 'display-title', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = '%s (%s)' % (self.dc.find('title').text, '%s-%s' % (self.min_year, self.max_year))

        ElementTree.SubElement(meta, 'display-item', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = 'Volume %s (%s)' % (self.get_volume_number(), self.get_year())

        ElementTree.SubElement(meta, 'browse-description', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'yes'
        }).text = self.dc.find('description').text

        ElementTree.SubElement(meta, 'year', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = self.get_year()

        ElementTree.SubElement(meta, 'facet-volume', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = 'Volume %d' % self.get_volume_number()

        ElementTree.SubElement(meta, 'human-readable-date', attrib={
            '{http://cdlib.org/xtf}meta': 'true',
            '{http://cdlib.org/xtf}facet': 'no',
            '{http://cdlib.org/xtf}tokenize': 'no'
        }).text = self.get_human_readable_date()

        return meta

    def get_position_data_from_pos(self, data_str, scale):
        '''
           Note: in PHP I used mb_convert_encoding($fields[4], "UTF-8", "ISO-8859-1") on 'text'
        '''
        output = []
        for line in data_str.split('\n'):
            fields = line.split('\t')
            try:
                output.append({
                    'x': int(float(fields[0]) * scale),
                    'y': int(float(fields[1]) * scale),
                    'w': int(float(fields[2]) * scale),
                    'h': int(float(fields[3]) * scale),
                    'text': fields[4]
                })
            except ValueError:
                continue
        return output

    def get_position_data_from_alto(self, xml, scale):
        '''
           Note: in PHP I used mb_convert_encoding($fields[4], "UTF-8", "ISO-8859-1") on 'text'
        '''
        fields = []
        for string in xml.findall('.//{http://www.loc.gov/standards/alto/ns-v2#}String'):
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

        try:
            data_str = open(self.file_dict['ocr_files'][i]).read()
        except UnicodeDecodeError:
            data_str = open(self.file_dict['ocr_files'][i], encoding='ISO-8859-1').read()

        try:
            xml = ElementTree.fromstring(data_str)
        except ElementTree.ParseError:
            return self.get_position_data_from_pos(data_str, scale)

        return self.get_position_data_from_alto(xml, scale)

    def get_structural_dict(self):
        data_str = open(self.file_dict['txt']).read()
        output = {}
        for line in data_str.split('\n'):
            fields = line.split('\t')
            if len(fields) < 2:
                continue
            if fields[0][0] == '0':
                output[fields[0]] = fields[1]
        return output 

    def newline_between_words(self, word1, word2):
        ''' The words are associative arrays with x, y, w, and h parameters.
            Check to see if there should be a newline between them. 

            If the left edge of word2 is to the left of the right edge of
            word1, there should be a newline between these words.

            If any part of word2 is above word1, there should be a
            newline between the words.

            +--------+ +--------+
            | WORD 1 | | WORD 2 | = false
            +--------+ +--------+
    
            +--------+ +--------+
            |        | | WORD 1 |
            +--------+ +--------+
                                  = true
            +--------+ +--------+
            | WORD 2 | |        |
            +--------+ +--------+
        '''

        if word2['x'] < (word1['x'] + word1['w']):
            return True

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
            return ' '.join([word['text'] for word in line['words']])
        else:
            return ''

    def spacing_to_string(self, spacing):
        return ' '.join([str(space) for space in spacing])

    def get_leaf(self, n):
        leaf_num = '%08d' % (n + 1)
        human_readable_leaf_num = str(n + 1)
        jpg_size = self.get_jpg_size(n)

        leaf = ElementTree.Element('leaf', attrib={
            'leafNum': human_readable_leaf_num,
            'type': '',
            'access': 'true',
            'imgFile': '%s.jpg' % leaf_num,
            'x': str(jpg_size[0]),
            'y': str(jpg_size[1]),
            'humanReadableLeafNum': human_readable_leaf_num,
            '{http://cdlib.org/xtf}sectionType': leaf_num
        })

        ElementTree.SubElement(leaf, 'cropBox', attrib={ 
            'x': str(jpg_size[0]),
            'y': str(jpg_size[1]),
            'w': str(jpg_size[0]),
            'h': str(jpg_size[1])
        })

        leaf_data = self.leaf_data_from_pos_data(n)
        #scale = self.get_jpg_tif_ratio(n)
        #leaf_data = self.scale_leaf_data(leaf_data, scale)

        # Add line spacing info to each line. This has to happen after scaling.
        i = 0
        while i < len(leaf_data):
            leaf_data[i]['spacing'] = self.get_line_spacing(leaf_data, i)
            i = i + 1

        l = 0
        for line in leaf_data:
            ElementTree.SubElement(leaf, 'line', attrib={
                'l': str(line['l']),
                't': str(line['t']),
                'r': str(line['r']),
                'b': str(line['b']),
                'spacing': self.spacing_to_string(line['spacing'])
            }).text = self.get_line_text(line)
            l = l + 1

        return leaf

    def get_xtf_converted_book(self):
        x = ElementTree.Element('xtf-converted-book')
        x.append(self.get_meta())
        for i in range(len(self.file_dict['ocr_files'])):
            x.append(self.get_leaf(i))
        return x

if __name__=='__main__':
    arguments = docopt(__doc__)

    mvol_path = '{}{}{}{}'.format(
        arguments['--local-root'],
        os.sep,
        arguments['<identifier>'].replace('-', os.sep),
        os.sep
    )

    # get OCR type. 
    if os.path.isdir('{}/ALTO'.format(mvol_path)):
        ocr_type = 'ALTO'
    elif os.path.isdir('{}/POS'.format(mvol_path)):
        ocr_type = 'POS'
    else:
        sys.stderr.write('no OCR data for {}\n'.format(arguments['<identifier>']))
        sys.exit(1)

    o = OCRBuilder({
            'dc': '{}{}.dc.xml'.format(mvol_path, arguments['<identifier>']),
            'jpgs': list_mvol_files(
                arguments['--local-root'], 
                arguments['<identifier>'],
                'JPEG'
            ),
            'ocr_files': list_mvol_files(
                arguments['--local-root'], 
                arguments['<identifier>'],
                ocr_type
            ),
            'tifs': list_mvol_files(
                arguments['--local-root'], 
                arguments['<identifier>'],
                'TIFF'
            ),
            'txt': '{}{}.struct.txt'.format(mvol_path, arguments['<identifier>'])
        }, 
        int(arguments['<min-year>']),
        int(arguments['<max-year>'])
    )
    
    xtf_converted_book = o.get_xtf_converted_book()
    print(ElementTree.tostring(xtf_converted_book, encoding='utf-8', method='xml').decode('utf-8'))
