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

def formatter(result):
    sites = set()
    tanks = set()
    return_result = []
    temp_data = {}
    for each in result:
        sites.add(each['site_name'])

    for site in sites:
        for data in result:
            if data['site_name'] == site and temp_data.get('site_name') == None and data['tank'] not in tanks:
                temp_data['site_name'] = data['site_name']
                temp_data['longitude'] = data['longitude']
                temp_data['latitude'] = data['latitude']
                temp_data['tanks'] = [[data['tank']]]
                tanks.add(data['tank'])
                continue
            if data['site_name'] == site and temp_data.get('site_name') == site and data['tank'] not in tanks:
                temp_data['tanks'].append([data['tank']])
                tanks.add(data['tank'])

        return_result.append(temp_data)
        temp_data = {}

    return return_result

def get_tanklogs_count(site_ids, tank_ids, start, end, limit, offset):
    with connection.cursor() as c:
        query = """
                SELECT 
                    COUNT(l.pv)
                FROM
                    (atg_primary_log l
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index AND t.Tank_controller = l.controller_type)
                WHERE
                    s.Site_id IN %s
                        AND t.Tank_id IN %s
                        AND 0+l.pv BETWEEN 0.1 AND 1000000
                        AND l.read_at BETWEEN %s AND %s
                        AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT %s, %s;
        """
        c.execute(query, [tuple(site_ids), tuple(tank_ids), start, end, offset, limit])
        data = c.fetchone()[0]
    return data


def get_tanklogs(site_ids, tank_ids, start, end, limit, offset):
    with connection.cursor() as c:
        query = """
                SELECT 
                    s.Name AS 'Site Name',
                    s.Site_id as 'siteId',
                    t.Name AS 'Tank Name',
                    t.Tank_id AS 'Tank_id',
                    t.Capacity AS 'Tank Capacity',
                    t.UOM AS 'Unit',
                    t.Display_unit AS 'Display Unit',
                    l.multicont_polling_address AS 'Controller polling address',
                    l.tank_index AS 'Tank index',
                    l.pv AS 'Volume',
                    l.sv AS 'Height',
                    l.read_at AS 'Log Time',
                    l.controller_type AS 'Controller_type'
                FROM
                    (atg_primary_log l force INDEX (indx_read_at) 
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index AND t.Tank_controller = l.controller_type)
                WHERE
                    s.Site_id IN %s
                        AND t.Tank_id IN %s
                        AND 0+l.pv BETWEEN 0.1 AND 1000000
                        AND l.read_at BETWEEN %s AND %s
                        AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT %s, %s;
        """
        c.execute(query, [tuple(site_ids), tuple(tank_ids), start, end, offset, limit])
        data = dictfetchall(c)
    return data

def get_anomaly_logs():
    with connection.cursor() as c:
        query = """
                SELECT 
                    s.Name AS 'Site Name',
                    s.Site_id as 'siteId',
                    t.Name AS 'Tank Name',
                    t.Tank_id AS 'Tank_id',
                    l.read_at AS 'Log Time',
                FROM
                    (atg_primary_log l force INDEX (indx_read_at) 
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index AND t.Tank_controller = l.controller_type)
                WHERE
                    s.Site_id IN %s
                        AND t.Tank_id IN %s
                        AND 0+l.pv BETWEEN 0.1 AND 1000000
                        AND l.read_at BETWEEN %s AND %s
                        AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT %s, %s;
        """
        c.execute(query)
        data = dictfetchall(c)
    return data


def revamped_get_tanklogs(tank_ids, start, end, limit, offset):
    with connection.cursor() as c:
        query = """
                    SELECT 
                        l.siteName AS 'Site Name',
                        l.Site_id as 'siteId',
                        l.Tank_name AS 'Tank Name',
                        l.Tank_id AS 'Tank_id',
                        l.Capacity AS 'Tank Capacity',
                        l.UOM AS 'Unit',
                        l.Display_unit AS 'Display Unit',
                        l.multicont_polling_address AS 'Controller polling address',
                        l.tank_index AS 'Tank index',
                        l.pv AS 'Volume',
                        l.sv AS 'Height',
                        l.read_at AS 'Log Time',
                        l.controller_type AS 'Controller_type'
                    FROM 
                        atg_primary_log l
                    WHERE
                            l.Tank_id IN %s
                            AND l.read_at BETWEEN %s AND %s
                            AND l.flag_log = 1
                    ORDER BY l.read_at DESC
                    LIMIT %s, %s;
                """
        c.execute(query, [tuple(tank_ids), start, end, offset, limit])
        data = dictfetchall(c)
    return data



def get_specific_tank_reading(tank_id):
    with connection.cursor() as c:
        query = """
                SELECT 
                    s.Name AS 'Site Name',
                    s.Site_id as 'siteId',
                    t.Name AS 'Tank Name',
                    t.Tank_id AS 'Tank_id',
                    t.UOM AS 'Unit',
                    t.Display_unit AS 'Display Unit',
                    l.pv AS 'Volume',
                    l.sv AS 'Height',
                    t.Offset AS 'Current Offset value',
                    l.read_at AS 'Log Time'
                FROM
                    (atg_primary_log l
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index
                        AND t.Tank_controller = l.controller_type)
                WHERE
                    t.Tank_id = %s
                    AND
                    0+l.pv BETWEEN 0.1 AND 1000000
                    AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT 5;
        """
        c.execute(query, [tank_id])
        data = dictfetchall(c)
    return data

def get_tankgrouplogs_count(tankgroup_ids, start, end, limit, offset):
    with connection.cursor() as c:
        query = """
                SELECT
                    COUNT(l.pv) 
                FROM
                    (atg_primary_log l
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index AND t.Tank_controller = l.controller_type)
                    JOIN backend_tankgroups_Tanks tgt ON tgt.tanks_id = t.Tank_id
                    JOIN backend_tankgroups tg  ON tg.Group_id = tgt.tankgroups_id
                WHERE
                    tgt.tankgroups_id IN %s
                        AND 0+l.pv BETWEEN 0.1 AND 1000000
                        AND l.read_at BETWEEN %s AND %s
                        AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT %s, %s;
        """
        c.execute(query, [tuple(tankgroup_ids), start, end, offset, limit])
        data = c.fetchone()[0]
    return data

def get_tankgroup_logs(tankgroup_ids, start, end, limit, offset):
    with connection.cursor() as c:
        query = """
                SELECT 
                    tg.Name AS 'TankGroup Name',
                    tg.Group_id AS 'TankGroupId',
                    s.Name AS 'Site Name',
                    s.Site_id as 'siteId',
                    t.Name AS 'Tank Name',
                    t.Tank_id AS 'Tank_id',
                    t.Capacity AS 'Tank Capacity',
                    t.UOM AS 'Unit',
                    t.Display_unit AS 'Display Unit',
                    l.multicont_polling_address AS 'Controller polling address',
                    l.tank_index AS 'Tank index',
                    l.pv AS 'Volume',
                    l.sv AS 'Height',
                    l.read_at AS 'Log Time',
                    l.controller_type AS 'Controller_type'
                FROM
                    (atg_primary_log l
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index AND t.Tank_controller = l.controller_type)
                    JOIN backend_tankgroups_Tanks tgt ON tgt.tanks_id = t.Tank_id
                    JOIN backend_tankgroups tg  ON tg.Group_id = tgt.tankgroups_id
                WHERE
                    tgt.tankgroups_id IN %s
                        AND 0+l.pv BETWEEN 0.1 AND 1000000
                        AND l.read_at BETWEEN %s AND %s
                        AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT %s, %s;
        """
        c.execute(query, [tuple(tankgroup_ids), start, end, offset, limit])
        data = dictfetchall(c)
    return data

def modified_get_tank_latest_log(Tank_controller,Tank_index,Controller_polling_address,mac_address,Display_unit,Unit,Capacity,Tank_name,Site_name,Product): 
    with connection.cursor() as c:
        query = """
                     SELECT
                        l.pv AS Volume,
                        l.sv AS Height,
                            (CASE
                                WHEN l.temperature IS NULL THEN '0.00'
                                ELSE l.temperature
                            END) AS temperature,
                            (CASE
                                WHEN l.water IS NULL THEN '0.00'
                                ELSE l.water
                            END) AS water,
                            l.read_at AS last_updated_time
                                
                        FROM
                            atg_primary_log l
                        WHERE
                            l.Controller_type = %s
                                AND l.tank_index = %s
                                AND l.multicont_polling_address = %s
                                AND l.flag_log = 1
                                AND l.device_address= %s
                        ORDER BY l.read_at DESC
                        LIMIT 1; 
                """
        c.execute(query, (Tank_controller,Tank_index,Controller_polling_address, mac_address))
        
        data = dictfetchall(c)
        if len(data) == 1:
            data[0]['Display Unit']=Display_unit
            data[0]['Unit']=Unit
            data[0]['Capacity']=Capacity
            data[0]['Tank Name']=Tank_name
            data[0]['siteName']=Site_name
            data[0]['Product']=Product
            data[0]['Tank_controller']=Tank_controller         
            data = log_utils.update_tankgroup_records(data)
        else:
            data.append(
                {
                'Display Unit':Display_unit,
                'Unit':Unit,
                'Capacity':Capacity,
                'Tank Name':Tank_name,
                'siteName':Site_name,
                'Tank_controller':Tank_controller,
                'Product':Product,
                'Fill %':0,
                'last_updated_time':'N/A'

                }
            )
    return data


def get_tank_latest_log(tank_id):
    with connection.cursor() as c:
        query = """
                    SELECT 
                        sub.*,
                        ta.alarm_type AS Alarm_type,
                        (CASE
                            WHEN
                                ta.alarm_type IS NOT NULL
                                    AND (DATEDIFF(NOW(), ta.last_time_mail_sent) <= 2)
                            THEN
                                'Active'
                            ELSE 'Inactive'
                        END) AS Alarm_status
                    FROM
                        (SELECT 
                            l.pv AS Volume,
                                l.sv AS Height,
                                (CASE
                                    WHEN l.temperature IS NULL THEN '0.00'
                                    ELSE l.temperature
                                END) AS temperature,
                                (CASE
                                    WHEN l.water IS NULL THEN '0.00'
                                    ELSE l.water
                                END) AS water,
                                l.read_at AS last_updated_time,
                                l.tank_index AS tank_index,
                                l.device_address AS raspbPi_Address,
                                l.multicont_polling_address AS multicont_polling_address,
                                bs.Site_id AS Site_id,
                                bs.Name AS siteName,
                                bt.Name AS 'Tank Name',
                                bt.Tank_id AS 'Tank_id',
                                bt.Capacity AS 'Capacity',
                                bt.Reorder AS 'Reorder',
                                bt.LL_Level AS 'Deadstock',
                                bt.UOM AS 'Unit',
                                bt.Display_unit AS 'Display Unit',
                                l.controller_type AS Tank_controller,
                                bp.Name AS Product
                        FROM
                            atg_primary_log l
                        JOIN backend_devices bd ON bd.Device_unique_address = l.device_address
                        JOIN backend_sites bs ON bs.Device_id = bd.Device_id
                        JOIN backend_tanks bt ON bt.Site_id = bs.Site_id
                            AND bt.Tank_index = l.tank_index
                            AND bt.Controller_polling_address = l.multicont_polling_address
                            AND bt.Tank_controller = l.Controller_type
                        JOIN backend_products bp ON bp.Product_id = bt.Product_id
                        WHERE
                            bt.Tank_id = %s
                                AND 0 + l.pv BETWEEN 0.1 AND 1000000
                                AND l.flag_log = 1
                        ORDER BY l.read_at DESC
                        LIMIT 1) sub
                            LEFT JOIN
                        tank_alarm_dispatcher ta ON sub.`Tank_id` = ta.tank_id
                        AND ta.last_time_mail_sent = (SELECT 
                            MAX(last_time_mail_sent)
                        FROM
                            tank_alarm_dispatcher
                        WHERE
                            tank_id = sub.`Tank_id`
                        GROUP BY tank_id);
            """
        c.execute(query, (tank_id,))
        data = dictfetchall(c)
    return data

def revamped_get_tankgroup_tank_latest_log(tank_id):
    with connection.cursor() as c:
        query = """
                    SELECT 
                    Volume,
                    Height,
                    last_updated_time,
                    Site_id,
                    siteName,
                    Tank_name AS 'Tank Name',
                    Capacity,
                    Unit,
                    DisplayUnit AS 'Display Unit'
  
                FROM
                    backend_latestatglog
                WHERE
                    Tank_id = %s;
            """
        c.execute(query, (tank_id,))
        data = dictfetchall(c)
    return data         

def get_tankgroup_tank_latest_log(tank_id):
    with connection.cursor() as c:
        query = """
                    SELECT 
                    l.pv AS Volume,
                    l.sv AS Height,
                    l.read_at AS last_updated_time,
                    l.tank_index AS tank_index,
                    l.multicont_polling_address AS multicont_polling_address,
                    bs.Site_id AS Site_id,
                    bs.Name AS siteName,
                    bt.Name AS 'Tank Name',
                    bt.Tank_id AS 'Tank_id',
                    bt.Capacity AS Capacity,
                    bt.UOM AS 'Unit',
                    bt.Display_unit AS 'Display Unit',
                    l.controller_type AS Tank_controller
                FROM
                    atg_primary_log l
                    JOIN backend_devices bd ON bd.Device_unique_address = l.device_address
                    JOIN backend_sites bs ON bs.Device_id = bd.Device_id
                    JOIN backend_tanks bt ON bt.Site_id = bs.Site_id and
                    bt.Tank_index = l.tank_index and bt.Controller_polling_address = l.multicont_polling_address
                    and bt.Tank_controller = l.Controller_type
                WHERE
                    bt.Tank_id = %s
                        AND 0+l.pv BETWEEN 0.1 AND 1000000
                        AND l.flag_log = 1
                ORDER BY l.read_at DESC
                LIMIT 1;
            """
        c.execute(query, (tank_id,))
        data = dictfetchall(c)
    return data


def get_tank_info(mac_address, tank_index):
    with connection.cursor() as c:
        query = """
            SELECT CalibrationChart, Offset, Density
            FROM `backend_tanks`
            WHERE `Site_id`	= (
                SELECT Site_id
                FROM `backend_sites`
                WHERE `Device_id` = (
                    SELECT Device_id
                    FROM `backend_devices`
                    WHERE Device_unique_address = %s
                )
            )
            AND `Tank_index` = %s;
        """
        c.execute(query, (mac_address, tank_index))
        data = dictfetchall(c)
    return data


def get_tanks_in_site(site_ids):
    with connection.cursor() as c:
        query = """
            SELECT s.Name as 'site_name', s.`Latitude` as latitude, s.`longitude`, d.`Device_unique_address` as device_Address, t.`Name` as tank
            FROM `backend_sites` as s
            JOIN `backend_tanks` as t
            ON s.Site_id = t.Site_id
            JOIN `backend_companies` as c
            ON s.`Company_id` = c.`Company_id`
            JOIN `backend_devices` as d
            ON c.`Company_id` = d.`Company_id`
            WHERE s.`Site_id` IN %s
            AND d.`Active` = 1;

        """

        c.execute(query, [tuple(site_ids)])
        result = dictfetchall(c)
        data = formatter(result)
    return data



def get_site_device_address(site_ids):
    with connection.cursor() as c:
        query = """
            SELECT s.Name, d.`Device_unique_address` as Device
            FROM `backend_sites` s
            JOIN `backend_devices`d
            ON s.`Device_id` = d.`Device_id`
            WHERE s.Site_id IN %s;
        """

        c.execute(query, [tuple(site_ids)])
        result = dictfetchall(c)
        data = format_to_dict(result)
    return data
