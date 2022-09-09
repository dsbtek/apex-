from django.db import connection


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def extract_all_tanks_details(tank_ids):
    with connection.cursor() as c:
        query = """
                SELECT 
                    tank.Tank_id AS tank_id,
                    tank.Tank_index AS tank_index,
                    tank.Controller_polling_address AS controller_polling_address,
                    tank.Tank_controller AS controller_type,
                    site.Site_id AS site_id,
                    site.Device_id AS device_id,
                    device.Device_unique_address AS mac_address,
                    site.Name AS site_name,
                    tank.Name AS tank_name,
                    tank.UOM AS unit,
                    tank.Capacity AS capacity,
                    bp.Name AS product
                FROM
                    backend_tanks tank
                        LEFT JOIN
                    backend_sites site ON tank.Site_id = site.Site_id
                        LEFT JOIN
                    backend_devices device ON device.Device_id = site.Device_id
                    JOIN backend_products bp ON bp.Product_id = tank.Product_id
                    WHERE tank.Tank_id IN %s
                """ 
        c.execute(query,[tuple(tank_ids)])
        data = dictfetchall(c)
    return data

def extract_tank_logs(tank_id, start, end):
    with connection.cursor() as c:
        query = """
                SELECT
                    s.Name AS site_name,
                    t.Name AS tank_name,
                    t.Tank_id AS tank_id,
                    l.pv AS Volume,
                    l.sv AS Height,
                    l.multicont_polling_address AS controller_address,
                    l.tank_index AS tank_index,
                    l.pv_flag AS flag,
                    l.controller_type AS controller_type,
                    l.read_at AS log_time,
                    DATE_FORMAT(l.read_at, '%%Y-%%m-%%d %%H') AS log_time_hour,
                    DATE_FORMAT(l.read_at, '%%Y-%%m-%%d') AS log_time_date,
                    t.Capacity AS capacity,
                    t.UOM AS Unit,
                    t.Display_unit AS 'Display Unit',
                    bp.Name as product 
                FROM
                    (atg_primary_log l force INDEX (indx_read_at) 
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.multicont_polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index
                        AND t.Tank_controller = l.controller_type
                    JOIN backend_products bp ON bp.Product_id = t.Product_id)
                WHERE
                    t.Tank_id = %s
                    AND
                    0+l.pv BETWEEN 0.1 AND 1000000
                    AND read_at BETWEEN %s AND %s
                ORDER BY l.read_at ASC
        """
        c.execute(query,[tank_id, start, end])
        data = dictfetchall(c)
        return data

def revampedextract_tank_logs(tank_id, start, end):
    with connection.cursor() as c:
        query = """
                SELECT
                    l.Name AS site_name,
                    l.Name AS tank_name,
                    l.Tank_id AS tank_id,
                    l.pv AS Volume,
                    l.sv AS Height,
                    l.multicont_polling_address AS controller_address,
                    l.tank_index AS tank_index,
                    l.pv_flag AS flag,
                    l.controller_type AS controller_type,
                    l.read_at AS log_time,
                    DATE_FORMAT(l.read_at, '%%Y-%%m-%%d %%H') AS log_time_hour,
                    DATE_FORMAT(l.read_at, '%%Y-%%m-%%d') AS log_time_date,
                    l.Capacity AS capacity,
                    l.UOM AS Unit,
                    l.Display_unit AS 'Display Unit',
                    l.Product_name as product 
                FROM
                    backend_tanklatestatgprimarylog l  
                WHERE
                    t.Tank_id = %s
                    AND
                    0+l.pv BETWEEN 0.1 AND 1000000
                    AND read_at BETWEEN %s AND %s
                ORDER BY l.read_at ASC
        """
        c.execute(query,[tank_id, start, end])
        data = dictfetchall(c)
        return data

def extract_tls_delivery_logs(tank_id, start_time, end_time):
    with connection.cursor() as c:
        query = """
                SELECT 
                    s.Name AS 'Site_name',
                    t.Name AS 'Tank_name',
                    DATE(l.system_end_time) AS 'Date',
                    l.volume AS 'Delivery',
                    l.system_start_time AS 'Delivery_start_time',
                    l.system_end_time AS 'Delivery_end_time',
                    t.UOM AS 'Unit',
                    bp.Name AS 'Product'
                FROM
                    (atg_integration_db.deliveries l
                    JOIN (backend_sites s
                    JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                    JOIN backend_tanks t ON s.Site_id = t.Site_id
                        AND l.polling_address = t.Controller_polling_address
                        AND l.tank_index = t.Tank_index
                        AND t.Tank_controller = l.controller_type
                    JOIN backend_products bp ON bp.Product_id = t.Product_id)
                WHERE l.system_start_time BETWEEN %s AND %s 
                AND t.Tank_id = %s
                ORDER BY l.system_start_time DESC;
            """ 
        c.execute(query, [start_time, end_time, tank_id])
        data = dictfetchall(c)
    return data
