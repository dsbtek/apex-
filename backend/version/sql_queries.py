from django.db import connection


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_devices_firmware():
    with connection.cursor() as c:
        query = """
                SELECT DISTINCT
                    d.Device_id AS 'Device_id',
                    d.Device_unique_address AS 'Device_address',
                    d.Name AS 'Serial_number',
                    s.Name AS 'Site_name',
                    f.version_number AS 'Current_version',
                    f.expected_version_number AS 'Expected_version',
                    f.updated_at AS 'Version_last_update'
                FROM
                    backend_devices d
                        LEFT JOIN
                    device_firmware_version f ON f.device_mac_address = d.Device_unique_address
                    JOIN backend_sites s ON s.Device_id = d.Device_id
                WHERE
                    (f.version_number IS NOT NULL
                        AND f.expected_version_number IS NOT NULL
                        AND f.updated_at IS NOT NULL)
                ORDER BY f.version_number ASC;

        """
        c.execute(query)
        data = dictfetchall(c)
    return data

def update_device_expected_firmware(devices, version):
    with connection.cursor() as c:
        query = """
                UPDATE device_firmware_version f
                        JOIN
                    backend_devices d ON f.device_mac_address = d.Device_unique_address 
                SET 
                    f.expected_version_number = %s
                WHERE
                    d.Device_id IN %s
        """

        c.execute(query, [version, tuple(devices)])
        count = c.rowcount
    
    if count > 0:
        return True
    else:
        return False