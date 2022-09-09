import csv
from rest_framework.response import Response
from rest_framework.views import exception_handler
from .users.serializer import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from functools import reduce
import json


class CustomResponse():

    def Success(data, status=200, headers=None):
        dta1 = {'data': data, 'errors': '',
                'code': status, 'status': 'success'}
        return Response(dta1, status, headers=headers)

    def Failure(error, status=400, headers=None):
        dta1 = {'data': '', 'errors': error,
                'code': status, 'status': 'failed'}
        return Response(dta1, status, headers=headers)


def parse_volume(volume):

    if type(volume) is str:
        volume = volume.replace(",", "").strip()
        return int(float(volume))

    return volume


def convert_csv_to_json(fullpath):
    data = []

    with open(fullpath, newline='') as chart:
        csv_reader = csv.DictReader(chart)
        headings = csv_reader.fieldnames
        columns = len(headings)
        for row in csv_reader:
            data_dict = {}
            for col in range(columns):
                data_dict.update({headings[col]: row[headings[col]]})
            data.append(data_dict)

        return data


class PaginationHandlerMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                                                self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


def replace_none_with_zero(all_date_summary_data):
    for eachDateDataDict in all_date_summary_data:
        for key, val in eachDateDataDict.items():
            if val is None:
                eachDateDataDict[key] = "0.00"

    return all_date_summary_data


def generate_product_details_for_date(product_name, transactions):
    ''' desired output format
        *********************************
        'PMS'
        [
            {'Pump': 'Pump2', 'Nozzle': '1', 'Volume': '720.0', 'Price': '160.0', 'Value(N)': '24600.0'},
            {'Pump': 'Pump1', 'Nozzle': '1', 'Volume': '20.0',  'Price': '160.0', 'Value(N)': '200.0'},
            {'Pump': '',      'Nozzle': '',  'Volume': '740.0', 'Price': '',      'Value(N)': '24800.0'}
        ]
        ************************************
    '''
    sales_transaction_details = []
    #trx_data = (json.loads(mydata[0]['dumpedTransaction']))
    trx_data = transactions

    filtered_product_data = filter(
        lambda trx: trx['Product_name'] == f'{product_name}', trx_data)  # filter product
    filtered_product_data_list = list(filtered_product_data)

    # initialize set() for uniqueness
    all_unique_pumps = set()
    all_unique_nozzles = set()
    all_unique_price_change = set()
    pump_name_to_mac_addr = {}

    for eachTransaction in filtered_product_data_list:
        all_unique_pumps.add(eachTransaction['Pump_mac_address'])
        all_unique_nozzles.add(eachTransaction['Nozzle_address'])
        all_unique_price_change.add(
            eachTransaction['Raw_transaction_price_per_unit'])
        pump_name_to_mac_addr[f'{eachTransaction["Pump_mac_address"]}'] = f'{eachTransaction["Pump_name"]}'

    unique_pumps = list(all_unique_pumps)
    unique_nozzles = sorted(all_unique_nozzles)
    unique_price_change = list(all_unique_price_change)

    for eachPump in unique_pumps:
        for eachNozzle in unique_nozzles:
            for eachPriceChange in unique_price_change:
                #print('Pump', eachPump,'nozz',eachNozzle,  'price', eachPriceChange)
                newTransactionData = filter(lambda mytrx: mytrx['Nozzle_address'] == f'{eachNozzle}' and mytrx['Pump_mac_address']
                                            == f'{eachPump}' and mytrx['Raw_transaction_price_per_unit'] == eachPriceChange, filtered_product_data_list)
                this_transactions = list(newTransactionData)
                this_amount = reduce(
                    lambda x, y: x + y['Transaction_raw_amount'], this_transactions, 0)
                this_vol = reduce(
                    lambda x, y: x + y['Transaction_raw_volume'], this_transactions, 0)

                if (this_vol == 0 and this_amount == 0):
                    continue
                sales_transaction_details.append(
                    {
                        "Pump": f'{pump_name_to_mac_addr[eachPump]}',
                        "Nozzle": f'{eachNozzle}',
                        "Volume": f'{this_vol}',
                        "Price": f'{eachPriceChange}',
                        "Value(N)": f'{this_amount}',
                    }
                )

    if len(sales_transaction_details) > 0:
        total_col_volume = reduce(
            lambda x, y: x + y['Transaction_raw_volume'], filtered_product_data_list, 0)
        total_col_amount = reduce(
            lambda x, y: x + y['Transaction_raw_amount'], filtered_product_data_list, 0)
        sales_transaction_details.append(
            {
                "Pump": f'Total',
                "Nozzle": f'',
                "Volume": f'{total_col_volume}',
                "Price": f'',
                "Value(N)": f'{total_col_amount}',
            }
        )
    else:
        sales_transaction_details.append(
            {
                "Pump": f'Total',
                "Nozzle": f'',
                "Volume": f'',
                "Price": f'',
                "Value(N)": f'',
            }
        )

    return sales_transaction_details


def append_date_sales_details(dateRange, passed_products, csvfile, all_dates_transactions_data):

    for eachdate in dateRange:
        filtered_date_transactions = filter(
            lambda trx: trx['date'] == f'{eachdate}', (all_dates_transactions_data))
        date_tranx_list = list(filtered_date_transactions)
        this_date_transaction = json.loads(
            date_tranx_list[0]['dumpedTransaction'])

        for each_product in passed_products:
            each_product_details = generate_product_details_for_date(
                each_product, this_date_transaction)
            writer = csv.DictWriter(
                csvfile, fieldnames=each_product_details[0].keys())
            # insert product_name on date	..i.e  Pms on 2021-10-09
            writer.writerows([{'Pump': f'{each_product} on {eachdate}'}])
            writer.writeheader()
            writer.writerows(each_product_details)
            # insert blank row
            writer.writerows([{'Pump': ''}])
            writer.writerows([{'Pump': ''}])


def generateSalesSummaryProductTotalizer(computed_data):
    initial_hearder = computed_data[0].keys()
    summationRow = {'date': 'Total'}
    # ommit the date key in the dict keys i.e. it comes 1st
    product_summary_header = (list(initial_hearder))[1:]
    for eachProductCalculated in product_summary_header:
        summaryValue = reduce(lambda x, y: x +
                              float(y[f'{eachProductCalculated}']), computed_data, 0)
        summationRow[f'{eachProductCalculated}'] = summaryValue

    return [summationRow]
