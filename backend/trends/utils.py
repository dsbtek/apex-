
import datetime
from builtins import range as _range
from ..smarteye_logs import utils 

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def processTrendData(datalist):
    final_dict = {}
    temp_dict = {}
    max_tank_capacity = 0

    converted_data = utils.update_tank_records(datalist)

    for data in converted_data:
        read_at = datetime.datetime.strptime(
            data["LogTime"], "%Y-%m-%d %H:%M:%S")
        label = read_at.strftime("%Y-%m-%d %H:%M")
        tank = data["Tank ID"]

        max_tank_capacity = max(max_tank_capacity, float(data['Volume']))

        if label in temp_dict:
            if tank not in temp_dict[label]:
                temp_dict[label][tank] = data['Volume']
        else:
            temp_dict[label] = {tank: data['Volume']}

    final_dict["trendsData"] = temp_dict
    final_dict["maxTankCapacity"] = max_tank_capacity+100.0

    return final_dict