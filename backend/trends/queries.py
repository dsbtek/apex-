
get_trend_data = """
    SELECT 
        s.Name AS 'Site Name',
        s.Site_id AS 'siteId',
        t.Tank_id AS 'Tank ID',
        t.Name AS 'Tank Name',
        t.UOM AS 'Unit',
        t.Display_unit AS 'Display Unit',
        l.pv AS 'Volume',
        l.sv AS 'Height',
        l.read_at AS 'LogTime',
        l.tank_index AS 'tankIndex',
        t.Capacity AS 'tankCapacity'
    FROM
        (atg_primary_log l force INDEX (indx_read_at) 
        JOIN (backend_sites s
        JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
        JOIN backend_tanks t ON s.Site_id = t.Site_id
            AND l.multicont_polling_address = t.Controller_polling_address
            AND l.tank_index = t.Tank_index
            AND t.Tank_controller = l.controller_type)
    WHERE
        t.Tank_id IN %s
            AND 0+l.pv BETWEEN 0.1 AND 1000000
            AND l.read_at BETWEEN %s AND %s
    ORDER BY l.read_at DESC;
"""