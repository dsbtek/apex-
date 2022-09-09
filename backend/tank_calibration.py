import sys
import csv
import io
import json
# import xlrd

MCPL_TANK1_CALIBRATION_CHART = [
    {"height": 0,    "volume": 0},
    {"height": 750,  "volume": 44950},
    {"height": 1516, "volume": 89950},
    {"height": 2283, "volume": 134900},
    {"height": 3046, "volume": 179800},
    {"height": 3812, "volume": 224700},
    {"height": 4575, "volume": 269600},
    {"height": 5343, "volume": 314500},
    {"height": 6111, "volume": 359400},
    {"height": 6874, "volume": 404300}
]

MCPL_TANK2_CALIBRATION_CHART = [
    {"height": 0,    "volume": 0},
    {"height": 798,  "volume": 44980},
    {"height": 1571, "volume": 89880},
    {"height": 2343, "volume": 134780},
    {"height": 3114, "volume": 179680},
    {"height": 3884, "volume": 224580},
    {"height": 4654, "volume": 269480},
    {"height": 5429, "volume": 314460},
    {"height": 6203, "volume": 359440}
]

HEIGHT_HEADER = "height"

VOLUME_HEADER = "volume"

INVALID_HEADINGS_CODE = 23


def get_volume(chart, height):

    height = float(height)

    if int(height) == 0:
        return 0.00

    prev_volume = 0
    prev_height = 0
    scale_factor = 0

    for calibration_data in chart:

        current_height = int(calibration_data[HEIGHT_HEADER])
        current_volume = int(calibration_data[VOLUME_HEADER])

        if (current_height - prev_height) != 0:
            scale_factor = (current_volume - prev_volume) / \
                (current_height - prev_height)

        if height > current_height:
            prev_height = current_height
            prev_volume = current_volume
        else:
            return compute_volume(prev_volume, height, prev_height, scale_factor)

    return compute_volume(prev_volume, height, prev_height, scale_factor)


def get_volume_from_chart(tank_index, height):

    if tank_index == 1:
        chart = MCPL_TANK1_CALIBRATION_CHART
    else:
        chart = MCPL_TANK2_CALIBRATION_CHART

    return get_volume(chart, height)


def compute_volume(prev_volume, height, prev_height, scale_factor):
    volume = (prev_volume) + ((height - prev_height) * scale_factor)
    return round(volume)


def parse_excel_file_to_json(uploaded_file):

    # TODO: Reactor cos read() is memory intensive for big files
    book = xlrd.open_workbook(file_contents=uploaded_file.read())

    sheet = book.sheet_by_index(0)
    content = []
    line_count = 0

    for rowx in range(sheet.nrows):
        cols = sheet.row_values(rowx)

        if line_count == 0:
            if not is_valid_headings(cols):
                return INVALID_HEADINGS_CODE
            line_count += 1
            continue

        line_count += 1

        row_dict = {}
        row_dict[HEIGHT_HEADER] = cols[0]
        row_dict[VOLUME_HEADER] = cols[1]

        content.append(row_dict)

    return json.dumps(content)


def parse_csv_file_to_json(uploaded_file):

    # TODO: Reactor cos read() is memory intensive for big files
    reader = csv.DictReader(io.StringIO(uploaded_file.read().decode('utf-8')))
    content = []

    if not is_valid_headings(reader.fieldnames):
        return INVALID_HEADINGS_CODE

    for row in reader:
        # DictReader ignores first row (headings)
        row_dict = {}
        row_dict[HEIGHT_HEADER] = row[HEIGHT_HEADER]
        row_dict[VOLUME_HEADER] = row[VOLUME_HEADER]
        content.append(row_dict)

    return json.dumps(content)


def is_valid_headings(heading):
    height_header = heading[0].strip()
    volume_header = heading[1].strip()

    if height_header != HEIGHT_HEADER or volume_header != VOLUME_HEADER:
        return False
    return True


def is_valid_file_type(uploaded_file):
    name = uploaded_file.name
    if name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv'):
        return True
    return False


def parse_file_to_json(uploaded_file):
    name = uploaded_file.name

    if name.endswith('.csv'):
        return parse_csv_file_to_json(uploaded_file)

    return parse_excel_file_to_json(uploaded_file)
