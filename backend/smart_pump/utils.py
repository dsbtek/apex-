
from backend import models
from datetime import datetime, timedelta
import datetime as datatimestr
from django.db.models import Sum

from backend.smart_pump.queries import get_total_value, get_total_volume
from .serializer import TransactionDataWithPumpNameSerializer
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime
from sigfig import round
from decouple import config
from .serializer import TransactionDataSerializer
from django.db import connection
import redis


def createProductPriceHistory(request):

    new_price = request.data['New Price']
    scheduled_time = datetime.strptime(
        request.data['Schedule Time'], "%Y-%m-%d %H:%M:%S")
    product_id = request.data['product_details']['Product_id']
    approver = request.user
    company = request.data['Company']
    company = models.Companies.objects.get(Company_id=company)
    product = models.Products.objects.get(Product_id=product_id)
    initial = True
    site = request.data['site_details']
    site = models.Sites.objects.get(Site_id=site)

    # Check if it is first price for company and site
    if models.ProductPriceHistory.objects.filter(Product=product, Company=company, Site=site).exists():
        initial = False

    product_price_history = models.ProductPriceHistory(
        Company=company, Site=site, Price=new_price, Sheduled_time=scheduled_time, Approved_by=approver, Product=product, Initial=initial)
    product_price_history.save()


def updateCompanyPriceOnProductPriceHistory(request):
    new_price = request.data['New Price']
    scheduled_time = datetime.strptime(
        request.data['Schedule Time'], "%Y-%m-%d %H:%M:%S")
    product_id = request.data['product_details']['Product_id']
    approver = request.user
    company_id = request.data['Company']
    company = models.Companies.objects.get(Company_id=company_id)
    product = models.Products.objects.get(Product_id=product_id)
    sites_in_company = models.Sites.objects.filter(Company=company_id)

    initial = True
    for each_site in sites_in_company:
        # Check if it is first price for company and site
        if models.ProductPriceHistory.objects.filter(Product=product_id, Company=company_id, Site=each_site.Site_id).exists():
            initial = False
        site_instance = models.Sites.objects.get(Site_id=each_site.Site_id)
        product_price_history = models.ProductPriceHistory(
            Company=company, Site=site_instance, Price=new_price, Sheduled_time=scheduled_time, Approved_by=approver, Product=product, Initial=initial)

        product_price_history.save()


def changeNozzlePrice(data):
    new_price = data['New Price']
    scheduled_time = datetime.strptime(
        data['Schedule Time'], "%y-%m-%d %I:%M:%S %p")
    product_id = data['product_details']['Product_id']
    site = data['site_details']['Site_id']

    pumps_in_site = models.Pump.objects.filter(Site=site).values()
    site = models.Sites.objects.get(Site_id=site)
    product = models.Products.objects.get(Product_id=product_id)

    for each_pump in pumps_in_site:
        devices = models.Devices.objects.filter(
            pk=each_pump['Device_id']).values()
        nozzles = models.Nozzle.objects.filter(Pump=each_pump['id']).values()
        mac_address = devices[0]['Device_unique_address']
        for nozzle in nozzles:
            if nozzle['Product_id'] == product_id:
                Nozzle_address = nozzle['Nozzle_address']
                newPriceChange = models.PriceChange(Site=site, Product=product, New_price=new_price, mac_address=mac_address,
                                                    Nozzle_address=Nozzle_address, Note="", Scheduled_time=scheduled_time, Received=False, Approved=True, Rejected=False)
                newPriceChange.save()


def getPumpOnlineStatus(mac_address):
    '''
    This connection is important if we need to always see the status of the pump/tank online. 
    '''
    r = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
    return r.get(f'pump_online_{mac_address}')

# get all nozzle dashboard details
def getAllNozzleDetailsInSite(site_id):
    response = []
    site_name = models.Sites.objects.get(Site_id=site_id).Name
    pumps = models.Pump.objects.filter(Site_id=site_id)

    nozzles = models.Nozzle.objects.filter(Pump_id__in=pumps)
    for nozzle in nozzles:
        this_pump = models.Pump.objects.get(id=nozzle.Pump_id)
        try:
            this_pump_mac = this_pump.Device.Device_unique_address
        except AttributeError:
            continue
        last_seen = getPumpOnlineStatus(this_pump_mac)
        product_name = models.Products.objects.get(
            Product_id=nozzle.Product_id).Name        
        latest_transaction = models.TransactionData.objects.all().order_by('Transaction_id').first()
        
        # latest_transaction = models.TransactionData.objects.filter(Site=site_id, Pump_mac_address=this_pump_mac, Nozzle_address=each_nozzle['Nozzle_address']).order_by('-Transaction_id').first()
        # Exclude the *continue* statement so that all nozzles are captured

        # if(not latest_transaction):
        #     continue
        try:
            nozzle_totalizer = latest_transaction.Transaction_stop_pump_totalizer_volume
            nozzle_price_per_unit = latest_transaction.Raw_transaction_price_per_unit
            nozzle_last_transact = latest_transaction.Transaction_stop_time
            # total_value =TransactionData.objects.filter(Site_id =latest_transaction.Site_id, Pump_mac_address=latest_transaction.Pump_mac_address, Nozzle_address=latest_transaction.Nozzle_address).aggregate(sum=Sum('Transaction_raw_amount'))['sum'] or 0.00
            # total_volume = models.TransactionData.objects.filter(Site_id =latest_transaction.Site_id, Pump_mac_address=latest_transaction.Pump_mac_address, Nozzle_address=latest_transaction.Nozzle_address).aggregate(sum=Sum('Transaction_raw_volume'))['sum'] or 0.00
            total_value = get_total_value(this_pump_mac,latest_transaction.Nozzle_address)
            total_volume = get_total_volume(this_pump_mac,latest_transaction.Nozzle_address)
        # exception thrown bcoz no transaction found on the nozzle.
        except AttributeError:
            nozzle_totalizer = 'N/A'
            nozzle_price_per_unit = 'N/A'
            nozzle_last_transact = 'N/A'
        
        calculated_flow_rate = latest_transaction.Transaction_raw_volume/(datetime.strptime(str(nozzle_last_transact), "%Y-%m-%d %H:%M:%S").minute)
        temp = {
            'pump_id': this_pump.id,
            'nozzle_name': nozzle.Name,
            'site_name': site_name,
            'pump_name': this_pump.Name,
            'pump_brand': this_pump.Pumpbrand.Name,
            'product': product_name,
            'calculated_flow_rate': round(calculated_flow_rate, sigfigs=3),
            'totalizer': nozzle_totalizer,
            'raw volume': latest_transaction.Transaction_raw_volume,
            'price_per_unit': nozzle_price_per_unit,
            'transaction_time': nozzle_last_transact,
            'status': last_seen,
            'last_updated_time': latest_transaction.Uploaded_time,
            'total_volume': round(total_volume, sigfigs = 9),
            'total_value': round(total_value, sigfigs = 9)
        }
        response.append(temp)
    return response

def getNozzleDetails(data):
    response = []
    site_name = models.Sites.objects.get(Site_id=data['site_id']).Name
    pump_name = models.Pump.objects.get(id=data['pump_id']).Name
    nozzles = models.Nozzle.objects.filter(id=data['nozzle_id'])
    for nozzle in nozzles:
        this_pump = models.Pump.objects.get(id=nozzle.Pump_id)
        try:
            this_pump_mac = this_pump.Device.Device_unique_address
        except AttributeError:
            continue
        last_seen = getPumpOnlineStatus(this_pump_mac)
        product_name = models.Products.objects.get(
            Product_id=nozzle.Product_id).Name        
        latest_transaction = models.TransactionData.objects.all().order_by('Transaction_id').first()
        
    # latest_transaction = models.TransactionData.objects.filter(Site=site_id, Pump_mac_address=this_pump_mac, Nozzle_address=each_nozzle['Nozzle_address']).order_by('-Transaction_id').first()
        # Exclude the *continue* statement so that all nozzles are captured

        # if(not latest_transaction):
        #     continue
        try:
            nozzle_totalizer = latest_transaction.Transaction_stop_pump_totalizer_volume
            nozzle_price_per_unit = latest_transaction.Raw_transaction_price_per_unit
            nozzle_last_transact = latest_transaction.Transaction_stop_time
        # exception thrown bcoz no transaction found on the nozzle.
        except AttributeError:
            nozzle_totalizer = 'N/A'
            nozzle_price_per_unit = 'N/A'
            nozzle_last_transact = 'N/A'
        
        calculated_flow_rate = latest_transaction.Transaction_raw_volume/(datetime.strptime(str(nozzle_last_transact), "%Y-%m-%d %H:%M:%S").minute)
        temp = {
            'pump_id': nozzles[0].Pump_id,
            'nozzle_name': nozzles[0].Name,
            'site_name': site_name,
            'pump_name': pump_name,
            'pump_brand': this_pump.Pumpbrand.Name,
            'product': product_name,
            'calculated_flow_rate': round(calculated_flow_rate, sigfigs=3),
            'totalizer': nozzle_totalizer,
            'raw volume': latest_transaction.Transaction_raw_volume,
            'price_per_unit': nozzle_price_per_unit,
            'transaction_time': nozzle_last_transact,
            'status': last_seen,
            'last_updated_time': latest_transaction.Uploaded_time,
        }
        response.append(temp)
    return response


def delaySendingReportStatus(dateRange, maxAllowedDays, reportDelayActive):
    if len(dateRange) > maxAllowedDays and reportDelayActive:
        return True
    else:
        return False


def getDateRange(request):
    sdate = datatimestr.datetime.strptime(
        request.GET['Start_time'], "%Y-%m-%d")   # start date
    edate = datatimestr.datetime.strptime(
        request.GET['End_time'], "%Y-%m-%d")   # end date

    def dates_bwn_twodates(start_date, end_date):
        for n in range(int((end_date - start_date).days + 1)):
            yield start_date + timedelta(n)

    return ([str(d).split(" ")[0] for d in dates_bwn_twodates(sdate, edate)])


def getSummaryForDate(Site_id, date, passed_products):
    # presentDateTransanctionsFilter = models.TransactionData.objects.filter(
    #     Site=Site_id, Transaction_stop_time__date=date)
    # presentDateTransactions = TransactionDataWithPumpNameSerializer(
    #     presentDateTransanctionsFilter, many=True)
    # transactions = {"date": f'{date}',
    #                 "transactions": presentDateTransactions.data}
    summary = {"date": date}

    def getAmountAndVolume(eachProduct):
        product_amount_with_volume = models.TransactionData.objects.filter(
            Product_name=eachProduct, Site=Site_id, Transaction_stop_time__date=date).aggregate(Sum('Transaction_raw_amount'), Sum('Transaction_raw_volume'))

        return [{f'{eachProduct.upper()}_N': product_amount_with_volume.get(
            'Transaction_raw_amount__sum')}, {f'{eachProduct.upper()}_L': product_amount_with_volume.get(
                'Transaction_raw_volume__sum')}]
    with ThreadPoolExecutor(max_workers=len(passed_products)) as executor:
        amount_with_volume_futures = [executor.submit(
            getAmountAndVolume,
            eachProduct) for eachProduct in passed_products]

        for price_volume_future in as_completed(amount_with_volume_futures):
            summary.update(price_volume_future.result()[0])
            summary.update(price_volume_future.result()[1])

    return {'summary': summary, 'transactions': [], }


def getSummaryReport(Site_id, passed_products, dateRange):

    summaryReport = []
    summaryTransactionsForDate = []
    # using thread to get transactions and summary for each date
    with ThreadPoolExecutor(max_workers=len(dateRange)) as executor:
        report_futures = [executor.submit(
            getSummaryForDate,
            Site_id, date, passed_products) for date in dateRange]

        for future in as_completed(report_futures):
            summaryReport.append(future.result().get('summary'))
            summaryTransactionsForDate.append(
                future.result().get('transactions'))

    # sort summary report by date since thread is asynchronous
    summaryReport.sort(
        key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))

    returnedData = {'SummaryReport': summaryReport,
                    'SummaryTransactionsForDate': summaryTransactionsForDate,
                    }
    return returnedData


class Report:
    def __init__(self, noz_adr, site, mac_adr, time_range, products):
        self.Nozzle_address = noz_adr
        self.Site_id = site
        self.Pump_mac_address = mac_adr
        self.transaction_time = time_range
        self.products = products

class TransactionHistoryFactory:
    def __init__(self, noz_adr, site, mac_adr, time_range, products):
        self.Nozzle_address = noz_adr
        self.Site_id = site
        self.Pump_mac_address = mac_adr
        self.transaction_time = time_range
        self.products = products

    def get_transaction_history_type(self):
        if (self.Pump_mac_address[0]) == '' and (self.Nozzle_address[0]) == '' and self.products[0] == '':
            return SiteandPeriodTransaction(self.Nozzle_address,self.Site_id,self.Pump_mac_address,self.transaction_time,self.products)
        elif (self.Pump_mac_address[0]) == '' and (self.Nozzle_address[0]) == '' and self.products[0] != '':
            return SitePeriodProductTransaction(self.Nozzle_address,self.Site_id,self.Pump_mac_address,self.transaction_time,self.products)
        elif len(self.Nozzle_address) > 0 and (self.Nozzle_address[0]) != '' and (self.products[0]) == '':   
            return SitePeriodNozzleTransaction(self.Nozzle_address,self.Site_id,self.Pump_mac_address,self.transaction_time,self.products)
        elif len(self.Nozzle_address) > 0 and len(self.products) > 0 and (self.Nozzle_address[0]) != '' and (self.products[0]) != '':
            return SitePeriodProductNozzleTransaction(self.Nozzle_address,self.Site_id,self.Pump_mac_address,self.transaction_time,self.products)

class SiteandPeriodTransaction(Report):
    def get_transactions(self):
        transactions =(models.TransactionData.objects.filter(
            Site=self.Site_id, Transaction_stop_time__range=self.transaction_time).order_by('-Transaction_stop_time'))
        return transactions

class SitePeriodProductTransaction(Report):
    def get_transactions(self):
        transactions = (models.TransactionData.objects.filter(
            Site=self.Site_id, Transaction_stop_time__range=self.transaction_time, Product_name__in=self.products).order_by('-Transaction_stop_time'))
        return transactions

class SitePeriodNozzleTransaction(Report):
    def get_transactions(self):
        transactions = (models.TransactionData.objects.filter(
            Site=self.Site_id, Transaction_stop_time__range=self.transaction_time, Nozzle_address__in=self.Nozzle_address,Pump_mac_address__in=self.Pump_mac_address).order_by('-Transaction_stop_time'))
        return transactions

class SitePeriodProductNozzleTransaction(Report):
    def get_transactions(self):
        transactions = (models.TransactionData.objects.filter(
            Site=self.Site_id, Transaction_stop_time__range=self.transaction_time, Nozzle_address__in=self.Nozzle_address, Pump_mac_address__in=self.Pump_mac_address, Product_name__in=self.products).order_by('-Transaction_stop_time'))
        return transactions