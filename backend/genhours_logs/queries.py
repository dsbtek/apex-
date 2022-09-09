
from django.db import connection


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def formatter(result):
    sites = set()
    return_result = []
    temp_data = {}
    for each in result:
        sites.add(each['site_name'])

    for site in sites:
        for data in result:
            if data['site_name'] == site and temp_data.get('site_name') == None:
                temp_data['site_name'] = data['site_name']
                temp_data['longitude'] = data['longitude']
                temp_data['latitude'] = data['latitude']
                temp_data['equipments'] = [[data['equipment']]]
                continue
            if data['site_name'] == site and temp_data.get('site_name') == site:
                temp_data['equipments'].append([data['equipment']])

        return_result.append(temp_data)
        temp_data = {}

    return return_result


def get_powermeterlogs(start, end, equipments):
    with connection.cursor() as c:
        query = """
            SELECT p.*, e.name as equipment
            FROM `backend_powermeterlogs` p
            JOIN `backend_equipment` e
            ON p.`equipment_id` = e.`id`
            WHERE timestamp BETWEEN %s AND %s
            AND `equipment_id` = %s
            ORDER BY timestamp DESC; 
        """

        c.execute(query, [start, end, tuple(equipments)])
        data = dictfetchall(c)
    return data


def get_equipments_in_site(site_ids):
    with connection.cursor() as c:
        query = """
            SELECT s.Name as 'site_name', s.`Latitude` as latitude, s.`longitude`, e.`name` as equipment
            FROM `backend_sites` as s
            JOIN `backend_equipment` as e
            ON s.Site_id = e.site_id
            WHERE s.`Site_id` IN %s;
        """

        c.execute(query, [tuple(site_ids)])
        result = dictfetchall(c)
        data = formatter(result)
    return data


def getStatusOfequipment(equipment_name, site_name):
    with connection.cursor() as c:
        query = """
            SELECT f.status, f.`timestamp`
            FROM `backend_flowmeterlogs` f
            JOIN `backend_devices` d
            ON d.`Device_unique_address` = f.`mac_address`
            JOIN `backend_sites` s
            ON s.`Device_id` = d.`Device_id`
            JOIN `backend_equipment` e
            ON e.`site_id` = s.`Site_id`
            WHERE e.`name` = %s
            AND s.Name = %s
            ORDER BY f.`timestamp` DESC
            LIMIT 1;
        """

        c.execute(query, (equipment_name, site_name))
        result = dictfetchall(c)
    return result
