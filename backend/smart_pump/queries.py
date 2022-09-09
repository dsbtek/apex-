
from django.db import connection
from backend import models
from . import utils as log_utils
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def format_to_dict(result):
    data = {}
    for each in result:
        data[each['Name']] = each['Device']
    return data


def get_total_value(Pump_mac_address, Nozzle_address):
    # Pump_mac_address="Pic-00002"
    query = """
                SELECT SUM(Transaction_raw_amount) 
                FROM smarteye_db.backend_transactiondata 
                WHERE Nozzle_address="{}" AND Pump_mac_address="{}";  
                """.format(Nozzle_address, Pump_mac_address)
    with connection.cursor() as c:
        c.execute(query)
        data = c.fetchall() #((5793512.888999994,),)
        data = data[0][0]
    return data


def get_total_volume(Pump_mac_address, Nozzle_address):
    query = """
                SELECT SUM(Transaction_raw_volume) 
                FROM smarteye_db.backend_transactiondata 
                WHERE Nozzle_address="{}" AND Pump_mac_address="{}";  
                """.format(Nozzle_address, Pump_mac_address)
    with connection.cursor() as c:
        c.execute(query)
        data = c.fetchall()
        data = data[0][0]
    return data
