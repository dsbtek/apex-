
from datetime import datetime, timedelta
from django.db import connection

from . import queries as q


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

def get_logs_within_range(start, end, tank_details):
    tank_index = str(tank_details['tank_index'])
    controller_address = str(tank_details['controller_polling_address'])
    controller_type = tank_details['controller_type']
    mac_address = tank_details['mac_address']
    site_id = tank_details['site_id']
    tank_id = tank_details['tank_id']

    query = """
                SELECT 
                    id,
                    multicont_polling_address,
                    device_address,
                    pv,
                    pv_flag,
                    tank_index,
                    sv,
                    read_at,
                    db_fill_time,
                    controller_type,
                    temperature,
                    water,
                    tc_volume,
                    DATE_FORMAT(read_at, '%%Y-%%m-%%d %%H') AS read_at_time,
                    DATE_FORMAT(read_at, '%%Y-%%m-%%d') AS read_date
                FROM
                    atg_primary_log
                WHERE
                    tank_index = %s
                        AND 0+pv BETWEEN 0.1 AND 1000000
                        AND multicont_polling_address = %s
                        AND controller_type = %s
                        AND device_address = %s
                        AND read_at BETWEEN %s AND %s
                ORDER BY read_at ASC
            """
    with connection.cursor() as c:
        c.execute(query,[tank_index,controller_address,controller_type,mac_address,start,end])
        data = c.fetchall()
    # return data
    vega_probes_tanks = [82, 83, 64, 65, 260, 280]
    # forte_probe = [260]

    if tank_id in vega_probes_tanks:
        newData = ()
        for d in data:
            d = list(d)
            d[3] = "{0:.3f}".format(float(d[3])*1000)
            d = tuple(d)
            newData += (d,)
        data = newData

    # if tank_id in forte_probe:
    #     newData = ()
    #     for d in data:
    #         x = d[3]
    #         d = list(d)
    #         d[3] = "{0:.3f}".format(float(d[6])*1000)
    #         d[6] = "{0:.3f}".format(float(x)*1000)
    #         d = tuple(d)
    #         newData += (d,)
    #     data = newData


    return data


def consumption_report(data, report_type, tank_details):
    payload = []
    data_length = len(data)
    if data_length > 0:
        start_hour = data[0][13]
        last_hour = data[-1][13]
        start_time = data[0][7]
        end_time = data[-1][7]
        start_date = data[0][14]
        end_date = data[-1][14]
        if report_type=='Hourly':
            # hour_stocks = [stock for stock in data if start_hour in stock]
            # test = extract_log_details_per_hour_stamp(hour_stocks, tank_details)
            while(datetime.strptime( start_hour, "%Y-%m-%d %H") <= datetime.strptime( last_hour, "%Y-%m-%d %H")):
                hour_stocks = [stock for stock in data if start_hour in stock]
                if len(hour_stocks):
                    log = extract_log_details_per_hour_stamp(hour_stocks, tank_details)
                    payload.append(log)
                
                hour = datetime.strptime(start_hour, "%Y-%m-%d %H")
                current_hour_plus_one = hour + timedelta(hours=1)
                start_hour = datetime.strftime(current_hour_plus_one, "%Y-%m-%d %H")
        elif report_type=='Daily':
            while(datetime.strptime(start_date, "%Y-%m-%d") <= datetime.strptime(end_date, "%Y-%m-%d")):
                date_stocks = [stock for stock in data if start_date in stock]
                if len(date_stocks):
                    log = extract_log_details_per_date_stamp(date_stocks, tank_details)
                    payload.append(log)
                
                date = datetime.strptime(start_date, "%Y-%m-%d")
                current_date_plus_one = date + timedelta(days=1)
                start_date = datetime.strftime(current_date_plus_one, "%Y-%m-%d")
        else:
            log = extract_log_details_in_hour_range(data, tank_details)

            log['Start_time'] = start_time
            log['End_time'] = end_time
            payload.append(log)

    return payload


def extract_log_details_in_hour_range(stocks, tank_details):
    first_inserted_row = stocks[0]
    last_inserted_row = stocks[len(stocks)-1]
    product = tank_details['product']
    site_name = tank_details['site_name']
    tank_name = tank_details['tank_name']
    unit = tank_details['unit']
    capacity = tank_details['capacity']
    opening_pv = first_inserted_row[3]
    closing_pv = last_inserted_row[3]
    opening_sv = first_inserted_row[6]
    closing_sv = last_inserted_row[6]
    start_db_fill_time = datetime.strftime(first_inserted_row[8], "%Y-%m-%d %H:%M:%S")
    end_db_fill_time = datetime.strftime(last_inserted_row[8], "%Y-%m-%d %H:%M:%S") 
    
    #since the loop goes through the data for each day, and there can be more than one delivery per day,
    # create variable to extract volume change per delivery and another one to capture the eventual
    # total    
    total_delivered_this_hour = 0
    
    current_delivery_capture_flag = False
    current_volume_at_delivery_start = 0
    current_volume_at_delivery_stop = 0

    for (index, (id,multicont_polling_address, device_address,pv,pv_flag,tank_index,sv,read_at,db_fill_time,controller_type,temperature,water,tc_volume, read_at_hour, read_date) ) in enumerate(stocks):
        #algorithm to extract delivery
        #pv_flag 1 means same level
        #pv_flag 2 means consumption
        #pv_flag 3 means delivery

        #if the flag is 3 and no previous delivery has started i.e current_capture_flag is 'stop'
        #change current_capture_flag to start and trace the previous log using index because that the
        #previous log is true start of the delivery
        if(index==0 and int(pv_flag) == 3 and not current_delivery_capture_flag):
            current_delivery_capture_flag = True
            
            try:                       
                current_volume_at_delivery_start =  pv
            except: 
                print("no previous log at start")

        elif(int(pv_flag) == 3 and not current_delivery_capture_flag ):
            current_delivery_capture_flag = True
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                if(int(previous_log_pv_flag) != 3)  :                          
                    current_volume_at_delivery_start =  previous_log[3]
            except: 
                print("no previous log at start")

        #if the flag is 2 and a delivery delivery has started i.e current_capture_flag is 'start'
        #change current_capture_flag to stop and trace the previous log using index because that the
        #previous log is true end of the delivery

        elif ((int(pv_flag) == 2 or int(pv_flag)==1) and current_delivery_capture_flag ):
            current_delivery_capture_flag = False
                           
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  previous_log[3]
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                total_delivered_this_hour = total_delivered_this_hour + quantity_delivered_here
            except: 
                print("no previous log at stop")

        elif (index==(len(stocks)-1) and current_delivery_capture_flag):
            current_delivery_capture_flag = False
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  pv
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                total_delivered_this_hour = total_delivered_this_hour + quantity_delivered_here
            except: 
                print("no previous log at stop")

    if total_delivered_this_hour < 300:
        total_delivered_this_hour = 0
    
    opening_percent = "{0:.3f}".format((float(opening_pv) / float(capacity))*100)
    closing_percent = "{0:.3f}".format((float(closing_pv) / float(capacity))*100)
    consumption = (float(opening_pv)+float(total_delivered_this_hour))-float(closing_pv)

    log = {
        'Site_name': site_name, 'Tank_name': tank_name,
        'Opening_stock': opening_pv,'OpeningPercentage': opening_percent, 'Closing_stock': closing_pv,
        'ClosingPercentage': closing_percent, 'Consumption': consumption, 'Delivery': str(total_delivered_this_hour),
        'Unit': unit, 'Product': product
                    }
    return log


def extract_log_details_per_hour_stamp(stocks, tank_details):
    first_inserted_row = stocks[0]
    last_inserted_row = stocks[len(stocks)-1]
    product = tank_details['product']
    site_name = tank_details['site_name']
    tank_name = tank_details['tank_name']
    unit = tank_details['unit']
    capacity = tank_details['capacity']
    opening_pv = first_inserted_row[3]
    closing_pv = last_inserted_row[3]
    opening_sv = first_inserted_row[6]
    closing_sv = last_inserted_row[6]
    start_db_fill_time = datetime.strftime(first_inserted_row[8], "%Y-%m-%d %H:%M:%S")
    end_db_fill_time = datetime.strftime(last_inserted_row[8], "%Y-%m-%d %H:%M:%S") 
    
    #since the loop goes through the data for each day, and there can be more than one delivery per day,
    # create variable to extract volume change per delivery and another one to capture the eventual
    # total    
    total_delivered_this_hour = 0
    
    current_delivery_capture_flag = False
    current_volume_at_delivery_start = 0
    current_volume_at_delivery_stop = 0

    for (index, (id,multicont_polling_address, device_address,pv,pv_flag,tank_index,sv,read_at,db_fill_time,controller_type,temperature,water,tc_volume, read_at_hour, read_date) ) in enumerate(stocks):
        #algorithm to extract delivery
        #pv_flag 1 means same level
        #pv_flag 2 means consumption
        #pv_flag 3 means delivery

        #if the flag is 3 and no previous delivery has started i.e current_capture_flag is 'stop'
        #change current_capture_flag to start and trace the previous log using index because that the
        #previous log is true start of the delivery
        if(index==0 and int(pv_flag) == 3 and not current_delivery_capture_flag):
            current_delivery_capture_flag = True
            
            try:                       
                current_volume_at_delivery_start =  pv
            except: 
                print("no previous log at start")

        elif(int(pv_flag) == 3 and not current_delivery_capture_flag ):
            current_delivery_capture_flag = True
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                if(int(previous_log_pv_flag) != 3)  :                          
                    current_volume_at_delivery_start =  previous_log[3]
            except: 
                print("no previous log at start")

        #if the flag is 2 and a delivery delivery has started i.e current_capture_flag is 'start'
        #change current_capture_flag to stop and trace the previous log using index because that the
        #previous log is true end of the delivery

        elif ((int(pv_flag) == 2 or int(pv_flag)==1) and current_delivery_capture_flag ):
            current_delivery_capture_flag = False
                           
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  previous_log[3]
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                quantity_delivered_here = 0.00 if quantity_delivered_here < 300.00 else quantity_delivered_here
                total_delivered_this_hour = total_delivered_this_hour + quantity_delivered_here
            except: 
                print("no previous log at stop")

        elif (index==(len(stocks)-1) and current_delivery_capture_flag):
            current_delivery_capture_flag = False
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  pv
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                quantity_delivered_here = 0.00 if quantity_delivered_here < 300.00 else quantity_delivered_here
                total_delivered_this_hour = total_delivered_this_hour + quantity_delivered_here
            except: 
                print("no previous log at stop")

    if total_delivered_this_hour < 0:
        total_delivered_this_hour = 0
    
    opening_percent = "{0:.3f}".format((float(opening_pv) / float(capacity))*100)
    closing_percent = "{0:.3f}".format((float(closing_pv) / float(capacity))*100)
    consumption = (float(opening_pv)+float(total_delivered_this_hour))-float(closing_pv)

    log = {
        'Site_name': site_name, 'Tank_name': tank_name,'Date': read_at_hour,
        'Opening_stock': opening_pv,'OpeningPercentage': opening_percent, 'Closing_stock': closing_pv,
        'ClosingPercentage': closing_percent, 'Consumption': consumption, 'Delivery': str(total_delivered_this_hour),
        'Unit': unit, 'Product': product 
                    }
    return log


def extract_log_details_per_date_stamp(stocks, tank_details):
    first_inserted_row = stocks[0]
    last_inserted_row = stocks[len(stocks)-1]
    product = tank_details['product']
    tank_id = tank_details['tank_id']
    controller_type = tank_details['controller_type']
    site_name = tank_details['site_name']
    tank_name = tank_details['tank_name']
    unit = tank_details['unit']
    capacity = tank_details['capacity']

    opening_pv = first_inserted_row[3]
    closing_pv = last_inserted_row[3]
    opening_sv = first_inserted_row[6]
    closing_sv = last_inserted_row[6]
    start_db_fill_time = datetime.strftime(first_inserted_row[8], "%Y-%m-%d %H:%M:%S")
    end_db_fill_time = datetime.strftime(last_inserted_row[8], "%Y-%m-%d %H:%M:%S") 
    
    #since the loop goes through the data for each day, and there can be more than one delivery per day,
    # create variable to extract volume change per delivery and another one to capture the eventual
    # total    
    total_delivered_this_day = 0
    
    current_delivery_capture_flag = False
    current_volume_at_delivery_start = 0
    current_volume_at_delivery_stop = 0

    for (index, (id,multicont_polling_address, device_address,pv,pv_flag,tank_index,sv,read_at,db_fill_time,controller_type,temperature,water,tc_volume, read_at_hour, read_at_date) ) in enumerate(stocks):
        #algorithm to extract delivery
        #pv_flag 1 means same level
        #pv_flag 2 means consumption
        #pv_flag 3 means delivery

        #if the flag is 3 and no previous delivery has started i.e current_capture_flag is 'stop'
        #change current_capture_flag to start and trace the previous log using index because that the
        #previous log is true start of the delivery
        if(index==0 and int(pv_flag) == 3 and not current_delivery_capture_flag):
            current_delivery_capture_flag = True
            
            try:                       
                current_volume_at_delivery_start =  pv
            except: 
                print("no previous log at start")

        elif(int(pv_flag) == 3 and not current_delivery_capture_flag ):
            current_delivery_capture_flag = True
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                if(int(previous_log_pv_flag) != 3)  :                          
                    current_volume_at_delivery_start =  previous_log[3]
            except: 
                print("no previous log at start")

        #if the flag is 2 and a delivery delivery has started i.e current_capture_flag is 'start'
        #change current_capture_flag to stop and trace the previous log using index because that the
        #previous log is true end of the delivery

        elif ((int(pv_flag) == 2 or int(pv_flag)==1) and current_delivery_capture_flag ):
            current_delivery_capture_flag = False
                           
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  pv
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                quantity_delivered_here = 0.00 if quantity_delivered_here < 300.00 else quantity_delivered_here
                total_delivered_this_day = total_delivered_this_day + quantity_delivered_here
            except: 
                print("no previous log at stop")

        elif (index==(len(stocks)-1) and current_delivery_capture_flag):
            current_delivery_capture_flag = False
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  pv
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                quantity_delivered_here = 0.00 if quantity_delivered_here < 300.00 else quantity_delivered_here
                total_delivered_this_day = total_delivered_this_day + quantity_delivered_here
            except: 
                print("no previous log at stop")

    if total_delivered_this_day < 0:
        total_delivered_this_day = 0
    
    if controller_type=='TLS':
        deliveries = get_tls_delivery(read_at_date, tank_id)
        if deliveries:
            total_delivered_this_day = sum([float(delivery['Delivery']) for delivery in deliveries])
        else:
            total_delivered_this_day = 0

    opening_percent = "{0:.3f}".format((float(opening_pv) / float(capacity))*100)
    closing_percent = "{0:.3f}".format((float(closing_pv) / float(capacity))*100)
    consumption = (float(opening_pv)+float(total_delivered_this_day))-float(closing_pv)
    
    log = {
        'Site_name': site_name, 'Tank_name': tank_name,'Date': read_at_date,
        'Opening_stock': opening_pv,'OpeningPercentage': opening_percent, 'Closing_stock': closing_pv,
        'ClosingPercentage': closing_percent, 'Consumption': consumption, 'Delivery': str(total_delivered_this_day),
        'Unit': unit, 'Product':product 
                    }
    return log


def delivery_report(stocks,tank_details):
    site_name = tank_details['site_name']
    tank_name = tank_details['tank_name']
    unit = tank_details['unit']
    product = tank_details['product']
    total_delivered_this_hour = 0
    
    current_delivery_capture_flag = False
    current_volume_at_delivery_start = 0
    current_volume_at_delivery_stop = 0
    deliveries = []
    for (index, (id,multicont_polling_address, device_address,pv,pv_flag,tank_index,sv,read_at,db_fill_time,controller_type,temperature,water,tc_volume, read_at_hour, read_at_date) ) in enumerate(stocks):
        if(index==0 and int(pv_flag) == 3 and not current_delivery_capture_flag):
            current_delivery_capture_flag = True
            
            try:                       
                current_volume_at_delivery_start =  pv
                delivery_start_time = read_at
                sentinel = {'Site_name': site_name, 'Tank_name': tank_name,'Delivery_start_time': delivery_start_time, 'start_pv':current_volume_at_delivery_start, 'Unit': unit, 'Date': read_at_date, 'Product': product}
                deliveries.append(sentinel)

            except: 
                print("no previous log at start")

        elif(int(pv_flag) == 3 and not current_delivery_capture_flag ):
            current_delivery_capture_flag = True
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                if(int(previous_log_pv_flag) != 3)  :                          
                    current_volume_at_delivery_start =  previous_log[3]
                delivery_start_time = previous_log[7]
                sentinel = {'Site_name': site_name, 'Tank_name': tank_name,'Delivery_start_time': delivery_start_time, 'start_pv':current_volume_at_delivery_start, 'Unit': unit, 'Date': read_at_date, 'Product': product}
                deliveries.append(sentinel)
            except: 
                print("no previous log at start")

        elif ((int(pv_flag) == 2 or int(pv_flag)==1) and current_delivery_capture_flag ):
            current_delivery_capture_flag = False
                           
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  pv
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                total_delivered_this_hour = total_delivered_this_hour + quantity_delivered_here
                delivery_stop_time = read_at
                start_dict = deliveries[-1]
                start_dict['Delivery_end_time'] = delivery_stop_time
                start_dict['stop_pv'] = current_volume_at_delivery_stop
                delivery = float(start_dict['stop_pv']) - float(start_dict['start_pv'])
                start_dict['Delivery'] = 0 if delivery < 0 else delivery

            except: 
                print("no previous log at stop")

        elif (index==(len(stocks)-1) and current_delivery_capture_flag):
            current_delivery_capture_flag = False
            
            try:
                previous_log = stocks[index-1]
                previous_log_pv_flag = previous_log[4]
                current_volume_at_delivery_stop =  pv
                
                #at this stage, add the currently captured delivery to the total delivered for today
                quantity_delivered_here  = float(current_volume_at_delivery_stop) - float(current_volume_at_delivery_start)
                total_delivered_this_hour = total_delivered_this_hour + quantity_delivered_here
                delivery_stop_time = read_at
                start_dict = deliveries[-1]
                start_dict['Delivery_end_time'] = delivery_stop_time
                start_dict['stop_pv'] = current_volume_at_delivery_stop
                delivery = float(start_dict['stop_pv']) - float(start_dict['start_pv'])
                start_dict['Delivery'] = 0 if delivery < 0 else delivery
            except: 
                print("no previous log at stop")

    if total_delivered_this_hour < 0:
        total_delivered_this_hour = 0

    return [delivery for delivery in deliveries if delivery['Delivery'] >= 300.00]


def consumption_report_generator(report_type, start, end, tank_ids):
    tank_no = len(tank_ids)
    details = extract_all_tanks_details(tank_ids)
    reports = []
    for i in range(tank_no):
       logs = get_logs_within_range(start, end, details[i])
       report = consumption_report(logs,report_type, details[i])
       reports.extend(report)
    return reports

def delivery_report_generator(start, end, tank_ids):
    tank_no = len(tank_ids)
    details = extract_all_tanks_details(tank_ids)
    reports = []
    for i in range(tank_no):
       stock_log = get_logs_within_range(start, end, details[i])
       report = delivery_report(stock_log, details[i])

       reports.extend(report)
    return reports

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_tls_delivery(date, tank_id):
    with connection.cursor() as c:
        query = """
            SELECT 
                DATE(l.system_end_time) AS 'Date',
                l.volume AS 'Delivery'
            FROM
                (atg_integration_db.deliveries l
                JOIN (backend_sites s
                JOIN backend_devices d ON s.Device_id = d.Device_id) ON l.device_address = d.Device_unique_address
                JOIN backend_tanks t ON s.Site_id = t.Site_id
                    AND l.polling_address = t.Controller_polling_address
                    AND l.tank_index = t.Tank_index
                    AND t.Tank_controller = l.controller_type)
            WHERE DATE(l.system_start_time) = %s 
            AND t.Tank_id = %s;
        """ 
        c.execute(query, [date, tank_id])
        tls_data = dictfetchall(c)
        return tls_data