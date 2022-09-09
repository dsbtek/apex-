from . import new_custom_reports as r
from datetime import datetime


def get_consumption_report(tank_id, start, end, report_type):
    report_type = r.ConsumptionReportFactory().get_consumption_report_type(report_type)
    return report_type(tank_id, start, end).get_consumption_report()


def get_delivery_report(tank, start, end):
    # temporary fix to get delivery within timerage less than jan 28
    start_time = datetime.strptime(start, '%Y-%m-%d %H:%M')
    end_time = datetime.strptime(end, '%Y-%m-%d %H:%M')
    threshold = "2021-01-28 06:09"
    threshold_time = datetime.strptime(threshold, "%Y-%m-%d %H:%M")
    #print('Controller', tank, tank.Tank_controller, tank.Tank_id)
    if (tank.Tank_controller == 'TLS' and end_time > threshold_time):
        temp_report = []
        if (start_time < threshold_time):
            report_type = r.DeliveryReportFactory().get_delivery_report_type(tank.Tank_controller)
            temp_report.extend(report_type(
                tank.Tank_id, start, threshold).get_delivery_report())

            report_type = r.DeliveryReportFactory().get_delivery_report_type('MTC')
            deliveries = report_type(
                tank.Tank_id, threshold, end).get_delivery_report()
            temp_report.extend(deliveries)

        else:
            report_type = r.DeliveryReportFactory().get_delivery_report_type('MTC')
            deliveries = report_type(
                tank.Tank_id, start, end).get_delivery_report()
            temp_report.extend(deliveries)
        return temp_report

    report_type = r.DeliveryReportFactory().get_delivery_report_type(tank.Tank_controller)
    return report_type(tank.Tank_id, start, end).get_delivery_report()
