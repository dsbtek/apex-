from unicodedata import decimal
from rest_framework.views import APIView
from . import serializer
from .serializer import TransactionDataResponseSerializer
from .. import utils
from rest_framework import status
from backend import models
from ..permissions import IsActiveAuthenticated
from . import utils as u
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import operator
from decouple import config
from backend.tasks import send_sales_summary_report, send_price_change_notification_task
from django.db import IntegrityError, connection
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.response import Response
from backend.custom_pagination import HeaderLimitOffsetPagination, LargeResultsSetPagination, SmallResultsSetPagination


class TransactionSummary(APIView):
    serializer_class = serializer.TransactionDataSerializer

    def get(self, request):
        request_params_serialized_data = serializer.RequestParamsSerializer(
            data={'Site_id': request.GET['Site_id'], 'Start_time': request.GET['Start_time'], 'End_time': request.GET['End_time'], 'Products': request.GET['Products']})
        # validate incoming request query params
        if not request_params_serialized_data.is_valid():
            return utils.CustomResponse.Failure(request_params_serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        Site_id = request.GET['Site_id']
        # get date ranges
        dateRange = u.getDateRange(request)
        passed_products = request.GET['Products'].split(",")

        # check if to delay report
        delayThisReport = u.delaySendingReportStatus(dateRange, config(
            'REPORT_DELAY_MAX_DAYS', cast=int), config('REPORT_DELAY_ACTIVE', cast=bool))
        if delayThisReport:
            # send task to celery
            email_receiver = (request.user.Email)
            # string format here else Json unserializable
            mail_receiver_name = (f'{request.user}')
            send_sales_summary_report.delay(
                email_receiver, f'{mail_receiver_name}', dateRange, Site_id, passed_products)
            return utils.CustomResponse.Success({"message": "Generated Report will be sent to your registered email address!"}, status=status.HTTP_200_OK)

        returnedData = u.getSummaryReport(
            Site_id, passed_products, dateRange)

        return utils.CustomResponse.Success(returnedData, status=status.HTTP_200_OK)


class PicTransactionLoggerV2(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        id = request.GET['id']
        na = request.GET['na']
        stattime = request.GET['stattime']
        stoptime = request.GET['stoptime']
        rv = request.GET['rv']
        ra = request.GET['ra']
        ppu = request.GET['ppu']
        pma = request.GET['pma']
        tstatv = request.GET['tstatv']
        tstoptv = request.GET['tstoptv']
        tstata = request.GET['tstata']
        tstopta = request.GET['tstopta']
        de = request.GET['de']
        site = request.GET['site']

        count_log_fail = 0
        error = "No errors"
        this_device = get_object_or_404(models.Devices, pk=de)
        this_site = get_object_or_404(models.Sites, pk=site)

        models.TransactionData.objects.create(local_id=id, Nozzle_address=na, Transaction_start_time=stattime, Transaction_stop_time=stoptime,
                                              Transaction_raw_volume=rv, Transaction_raw_amount=ra,
                                              Raw_transaction_price_per_unit=ppu, Pump_mac_address=pma,
                                              Transaction_start_pump_totalizer_volume=tstatv, Transaction_stop_pump_totalizer_volume=tstoptv,
                                              Transaction_start_pump_totalizer_amount=tstata, Transaction_stop_pump_totalizer_amount=tstopta,
                                              Device=this_device, Site=this_site
                                              )

        return utils.CustomResponse.Success('success', status=status.HTTP_200_OK)


class PicTransactionConfirmation(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        id = request.GET['id']

        if models.TransactionData.objects.filter(local_id=id).exists():
            return Response('y', status=status.HTTP_201_CREATED)
        return Response('n', status=status.HTTP_201_CREATED)

class PicTransactionLogger(APIView):
    permission_classes = ()
    authentication_classes = ()
    def post(self, request, *args, **kwargs):
        count_log_fail = 0
        error = "No errors"
        message = "Creation was successful"
        transaction_data = request.data
        for items in transaction_data:
            '''
             index 0 - transaction_id
             index 1 - Nozzle_address
             index 2 - start_time
             index 3 - end_time
             index 4 - raw_volume
             index 5 - raw_amount
             index 6 - raw_ppu
             index 7 - mac_address
             index 8 - volume_Start_totalizer
             index 9 - volume_end_totalizer
             index 10 - amount_Start_totalizer
             index 11 - amount_end_totalizer
             index 12 - site
             index 13 - device
             index 14 - local_id / uniques identifier 
            '''

            this_device = get_object_or_404(models.Devices, pk=items[12])
            this_site = get_object_or_404(models.Sites, pk=items[13])
            nozzle_add = int(items[1], 16) # convert hexadecimal to decimal / whole number
            decimal_config = models.Nozzle.objects.filter(Pump__Device__Device_unique_address=items[7]).values()
            raw_volume = int(items[4]) / (10**decimal_config[0]['Decimal_setting_volume'])
            raw_amount = int(items[5]) / (10**decimal_config[0]['Decimal_setting_amount'])
            raw_upp = int(items[6]) / (10**decimal_config[0]['Decimal_setting_price_unit'])
           
            try:
                with transaction.atomic():
                    models.TransactionData.objects.create(
                                                        local_id=items[14], 
                                                        Nozzle_address=nozzle_add, 
                                                        Transaction_start_time=items[2], 
                                                        Transaction_stop_time=items[3],
                                                        Transaction_raw_volume=str(raw_volume), 
                                                        Transaction_raw_amount=str(raw_amount),
                                                        Raw_transaction_price_per_unit=str(raw_upp),
                                                        Pump_mac_address=items[7],
                                                        Transaction_start_pump_totalizer_volume=items[8],
                                                        Transaction_stop_pump_totalizer_volume=items[9],
                                                        Transaction_start_pump_totalizer_amount=items[10],
                                                        Transaction_stop_pump_totalizer_amount=items[11],
                                                        Device=this_device, Site=this_site,
                                                        Raw_nozzle_address = items[1]
                                                    )
            except IntegrityError as e:
                count_log_fail += 1
                error = e
                message = "Duplicate entry for Transaction ID '{}'".format(items[0])
        return utils.CustomResponse.Success("{0} log(s) failed: {1}".format(count_log_fail, message), status=status.HTTP_201_CREATED)


class TransactionLogger(APIView, LargeResultsSetPagination):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.TransactionDataSerializer

    def post(self, request):
        # fix for double transaction
        index = 0
        for each in request.data:
            if not models.TransactionData.objects.filter(local_id=each.get('local_id')).exists():
                passed_data = self.serializer_class(
                    data=request.data[index], many=False)
                if passed_data.is_valid():
                    passed_data.save()
            index = index + 1
        return utils.CustomResponse.Success('success', status=status.HTTP_201_CREATED)

    def get(self, request):
        ''' Min query params: Site and Time Range '''
        Nozzle_address = request.GET['Nozzle_addresses'].split(',')
        Site_id = request.GET['Site_id']
        Pump_mac_address = request.GET['Pump_mac_address'].split(',')
        transaction_time = request.GET['period'].replace("+", " ").split(",")
        products = request.GET['products'].split(",")

        transaction_history_type = u.TransactionHistoryFactory(
            Nozzle_address, Site_id, Pump_mac_address, transaction_time, products).get_transaction_history_type()
        # get transactions
        if transaction_history_type is not None:
            returned = transaction_history_type.get_transactions()
            results = self.paginate_queryset(returned, request, view=self)
            serializer = TransactionDataResponseSerializer(results, many=True)
            data, headers = self.get_paginated_response(serializer.data)
            # todo:Cache this response into Redis for later use
            return utils.CustomResponse.Success(data=data, headers=headers)

        else:
            return utils.CustomResponse.Failure('Invalid form/request data', status=status.HTTP_400_BAD_REQUEST)


class PicRemoteConfig(APIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.PicNozzleSerializer
    def post(self, request):
        nozzles = self.serializer_class(models.Nozzle.objects.filter(
            Pump__Device__Device_unique_address=request.data['mac_address'], Pump__Pushed_to_device=True, Pump__Activate=True), many=True)
        data = []
        for item in range(len(nozzles.data)):
            site_id = nozzles.data[item]['Site_id']
            Device_id = nozzles.data[item]['Device_id']
            Nozzle_count = nozzles.data[item]['Nozzle_count']
            Pump_protocol = nozzles.data[item]['Pump_protocol']
            Nozzle_addres = nozzles.data[item]['Nozzle_address']
            Nozzle_address_hex_code = nozzles.data[item]['Nozzle_address_hex_code']
            
            Price = nozzles.data[item]['Price']
            if not Price or Price == None:
                Price = "0.00"
            Price_time = nozzles.data[item]['Price_time']
            if not Price_time or Price_time == None:
                Price_time = datetime.now()

            Decimal_setting_price_unit = nozzles.data[item]['Decimal_setting_price_unit']
            Decimal_setting_amount = nozzles.data[item]['Decimal_setting_amount']
            Decimal_setting_volume = nozzles.data[item]['Decimal_setting_volume']
            data_pic_config = {
                    "Site_id": site_id,
                    "Device_id": Device_id,
                    "Nozzle_count": Nozzle_count,
                    "Pump_protocol": Pump_protocol,
                    "Nozzle_address": Nozzle_address_hex_code,
                    "Price": Price,
                    "Price_time": Price_time,
                    "Decimal_setting_price_unit": Decimal_setting_price_unit,
                    "Decimal_setting_amount": Decimal_setting_amount,
                    "Decimal_setting_volume": Decimal_setting_volume
                }
            data.append(data_pic_config)
        return utils.CustomResponse.Success(data, status=status.HTTP_200_OK)


class RemoteConfig(APIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.NozzleSerializer

    def get(self, request):
        nozzles = self.serializer_class(models.Nozzle.objects.filter(
            Pump__Device__Device_unique_address=request.data['mac_address'], Pump__Pushed_to_device=True, Pump__Activate=True), many=True)
        return utils.CustomResponse.Success(nozzles.data, status=status.HTTP_200_OK)


class PushConfigToDevice(APIView):
    '''
        Endpoint for pushing changes in remote config to device
    '''
    serializer_class = serializer.PumpSerializer

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        pump = get_object_or_404(models.Pump, pk=pk)
        pump.Pushed_to_device = True
        pump.save()
        serializer = self.serializer_class(pump)
        return utils.CustomResponse.Success(serializer.data)


class PriceChange(APIView):
    serializer_class = serializer.PriceChangeSerializer

    def get(self, request):
        serialized_data = self.serializer_class(models.PriceChange.objects.filter(
            mac_address=request.data['mac_address'], Approved=True, Received=False, Rejected=False), many=True)
        if len(serialized_data.data) > 0:
            models.PriceChange.objects.filter(
                mac_address=request.data['mac_address'], Approved=True, Received=False).update(Received=True)
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data, many=True)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request, pricechange_id):
        serialized_data = self.serializer_class(models.PriceChange.objects.get(
            pk=pricechange_id), data=request.data, partial=True)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_202_ACCEPTED)


class RawPriceChangeData(APIView):
    serializer_class = serializer.RawPriceChangeDataSerializer

    def get(self, request):
        serialized_data = serializer.GetRawPriceChangeDataSerializer(
            models.RawPriceChangeData.objects.filter(Site=request.GET['Site_id']), many=True)
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        pricechange_id = request.data.get('id', None)
        pc_status = request.data.get('Approval', None)
        models.RawPriceChangeData.objects.filter(
            pk=pricechange_id).update(Approved=pc_status)
        # split pricechange into nozzles in site
        if pc_status == True:
            u.changeNozzlePrice(request.data)
            return utils.CustomResponse.Success(data="Price change approved successfully", status=status.HTTP_201_CREATED)
        return utils.CustomResponse.Success(data="Price change rejected successfully", status=status.HTTP_201_CREATED)


class SitePriceChangeRequest(APIView):
    serializer_class = serializer.PriceChangeRequestSerializer

    def get(self, request):
        serialized_data = serializer.GetPriceRequestDataSerializer(
            models.PriceChangeRequestData.objects.filter(Site=request.GET['Site_id']), many=True)
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        serialized_data.save(Initiator=request.user)
        # Notify Company Admin of new price change request
        #price_change_request, designation, is_initial_price
        send_price_change_notification_task.delay(
            serialized_data.data, 'Site', True)
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        # endpoint to authorize/reject price change
        pricechange_id = request.data.get('id', None)
        pc_status = request.data.get('Approval', None)
        rejection_note = request.data.get('Rejection_note', None)
        models.PriceChangeRequestData.objects.filter(
            pk=pricechange_id).update(Approved=pc_status, Actor=request.user, Rejection_note=rejection_note, Approval_or_rejection_time=datetime.now())
        # create Product_Price_History Object
        if pc_status == True:
            u.createProductPriceHistory(request)
            # Notify Initiator of Price Approval
            deserialized_data = self.serializer_class(
                models.PriceChangeRequestData.objects.get(pk=pricechange_id))
            send_price_change_notification_task.delay(
                deserialized_data.data, 'Site', False)
            return utils.CustomResponse.Success(data="Price approved successfully", status=status.HTTP_201_CREATED)
        # notify initiator of Price Rejected
        deserialized_data = self.serializer_class(
            models.PriceChangeRequestData.objects.get(pk=pricechange_id))
        send_price_change_notification_task.delay(
            deserialized_data.data, 'Site', False)
        return utils.CustomResponse.Success(data="Price rejected successfully", status=status.HTTP_201_CREATED)


class CompanyPriceChangeRequest(APIView):
    serializer_class = serializer.CompanyProductPriceChangeRequestSerializer

    def get(self, request):
        serialized_data = serializer.GetCompanyPriceRequestDataSerializer(
            models.CompanyProductPriceRequest.objects.filter(Company=request.GET['Company_id']), many=True)
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        serialized_data.save(Initiator=request.user)
        # Notify Company Admin of new price change request for company
        # notification params:price_change_request object, designation, is_initial_price
        send_price_change_notification_task.delay(
            serialized_data.data, 'Company', True)
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        # endpoint to authorize/reject price change request for  all sites in a company
        pricechange_id = request.data.get('id', None)
        pc_status = request.data.get('Approval', None)
        rejection_note = request.data.get('Rejection_note', None)
        models.CompanyProductPriceRequest.objects.filter(
            pk=pricechange_id).update(Approved=pc_status, Actor=request.user, Rejection_note=rejection_note, Approval_or_rejection_time=datetime.now())
        # create Product_Price_History Object
        if pc_status == True:
            u.updateCompanyPriceOnProductPriceHistory(request)
            # Notify Initiator of Price Approval
            deserialized_data = self.serializer_class(
                models.CompanyProductPriceRequest.objects.get(pk=pricechange_id))
            send_price_change_notification_task.delay(
                deserialized_data.data, 'Company', False)
            return utils.CustomResponse.Success(data="Price approved successfully", status=status.HTTP_201_CREATED)
        # notify initiator of Price Rejection
        deserialized_data = self.serializer_class(
            models.CompanyProductPriceRequest.objects.get(pk=pricechange_id))
        send_price_change_notification_task.delay(
            deserialized_data.data, 'Company', False)
        return utils.CustomResponse.Success(data="Price rejected successfully", status=status.HTTP_201_CREATED)


class PriceExecutionLogger(APIView):
    '''API to track execution of new price on the device '''
    serializer_class = serializer.DevicePriceExecutionSerializer
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data, many=True)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)


class Pumps(APIView):
    serializer_class = serializer.PumpSerializer

    def get(self, request):
        deserialized_data = self.serializer_class(
            models.Pump.objects.all(), many=True)
        return utils.CustomResponse.Success(deserialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        pump_serialized_data = serializer.PumpSaveSerializer(data=request.data)
        if not pump_serialized_data.is_valid():
            return utils.CustomResponse.Failure(pump_serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        pump_exist = models.Pump.objects.filter(Name=request.data.get('Name', None), Device=request.data.get(
            'Device', None), Site=request.data.get('Site', None)).first()
        if not pump_exist:
            pump_serialized_data.save()
            pump_exist = pump_serialized_data.data

        nozzles = request.data['Nozzles']
        models.Devices.objects.filter(
            pk=request.data.get("Device", None)).update(Used=True)
        try:
            pump_reference = pump_exist.id
        except AttributeError:
            pump_reference = pump_exist['id']
        for each in nozzles:
            try:
                each['Pump'] = pump_exist.id
            except AttributeError:
                each['Pump'] = pump_exist['id']
        nozzle_serialized_data = serializer.NozzleSaveSerializer(
            data=nozzles, many=True)
        if not nozzle_serialized_data.is_valid():
            return utils.CustomResponse.Failure(nozzle_serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        nozzle_serialized_data.save()
        post_response_serializer = self.serializer_class(
            models.Pump.objects.get(
                pk=pump_reference))
        return utils.CustomResponse.Success(post_response_serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        pump_serialized_data = serializer.PumpSaveSerializer(models.Pump.objects.get(
            pk=request.data.get('id', None)), data=request.data, partial=True)
        if not pump_serialized_data.is_valid():
            return utils.CustomResponse.Failure(pump_serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        pump_serialized_data.save()

        nozzles = request.data['Nozzles']
        for each in nozzles:
            each['Pump'] = pump_serialized_data.data['id']
            try:
                each['Display_unit'] = each['Display_unit']['alias']
            except Exception as e:
                each['Display_unit'] = each['Display_unit']

            try:
                each['Product'] = each['Product']['Product_id']
            except Exception as e:
                each['Product'] = each['Product']

            try:
                self._extracted_from_patch_12(each)
            except Exception as e:
                pass

            try:
                nozzle_serialized_data = serializer.NozzleSaveSerializer(
                    models.Nozzle.objects.get(pk=each['id']), data=each, partial=True)
            except KeyError as e:
                product = models.Products.objects.get(pk=each['Product'])
                pump = models.Pump.objects.get(pk=each['Pump'])
                models.Nozzle(Name=each['Name'], Nozzle_address=each['Nozzle_address'], Decimal_setting_volume=each['Decimal_setting_volume'], Product=product, Pump=pump, Decimal_setting_price_unit=each['Decimal_setting_price_unit'],
                              Decimal_setting_amount=each['Decimal_setting_amount'], Totalizer_at_installation=each['Totalizer_at_installation'], Display_unit=each['Display_unit'], Nominal_flow_rate=each['Nominal_flow_rate']).save()

            if nozzle_serialized_data.is_valid():
                nozzle_serialized_data.save()
            else:
                return utils.CustomResponse.Failure(nozzle_serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)
        response_serializer = self.serializer_class(
            models.Pump.objects.get(
                pk=request.data.get('id', None)))
        return utils.CustomResponse.Success(response_serializer.data, status=status.HTTP_201_CREATED)

    def _extracted_from_patch_12(self, each):
        each.pop('identifier')
        each['Nozzle_address'] = int(each['Nozzle_address'])
        each['Decimal_setting_price_unit'] = int(
            each['Decimal_setting_price_unit'])
        each['Decimal_setting_amount'] = int(each['Decimal_setting_amount'])
        each['Decimal_setting_volume'] = int(each['Decimal_setting_volume'])
        each['Totalizer_at_installation'] = int(
            each['Totalizer_at_installation'])
        each['Nominal_flow_rate'] = int(each['Nominal_flow_rate'])
        each['First_initial_price'] = int(each['First_initial_price'])


class PumpsActivationDetails(APIView):
    serializer_class = serializer.PumpSerializer

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        pump = get_object_or_404(models.Pump, pk=pk)
        if pump.Activate:
            pump.Activate = False
            pump.save()
        else:
            pump.Activate = True
            pump.save()
        serializer = self.serializer_class(pump)
        return utils.CustomResponse.Success(serializer.data)


class Nozzle(APIView):
    serializer_class = serializer.NozzleSaveSerializer

    def get(self, request, *args, **kwargs):
        deserialized_data = self.serializer_class(
            models.Nozzle.objects.filter(Pump=request.data['Pump_id']), many=True)
        return utils.CustomResponse.Success(deserialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request, nozzle_id):
        serialized_data = self.serializer_class(models.Nozzle.objects.get(
            pk=nozzle_id), data=request.data, partial=True)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_202_ACCEPTED)


class PumpBrand(APIView):
    serializer_class = serializer.PumpBrandSerializer

    def get(self, request):
        deserialized_data = self.serializer_class(
            models.PumpBrand.objects.all(), many=True)
        return utils.CustomResponse.Success(deserialized_data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serialized_data = self.serializer_class(data=request.data)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.validated_data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        serialized_data = self.serializer_class(models.PumpBrand.objects.get(
            pk=request.data['id']), data=request.data, partial=True)
        if not serialized_data.is_valid():
            return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

        serialized_data.save()
        return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_200_OK)


class PumpsInSite(APIView):
    serializer_class = serializer.PumpSerializer

    def get(self, request):
        deserialized_data = self.serializer_class(models.Pump.objects.filter(
            Site__Site_id=request.GET['Site_id']), many=True)
        return utils.CustomResponse.Success(deserialized_data.data, status=status.HTTP_200_OK)


class NozzleDashboard(APIView):
    def get(self, request):
        response = u.getAllNozzleDetailsInSite(request.query_params.get('Site_id'))
        return utils.CustomResponse.Success(response, status=status.HTTP_200_OK)

class NozzleDetails(APIView):
    def get(self, request):
        response = u.getNozzleDetails(request.data)
        return utils.CustomResponse.Success(response, status=status.HTTP_200_OK)

class NozzleTrends(APIView):
    serializer_class = serializer.TransactionDataSerializer

    def get(self, request):
        Nozzle_address = request.GET['Nozzle_addresses'].split(',')
        Site_id = request.GET['Site_id']
        pump_id = request.GET['pump_id']
        Pump_mac_address = request.GET['Pump_mac_address']
        transaction_time = request.GET['period'].split(",")
        transaction_queryset = models.TransactionData.objects.filter(
            Site=Site_id, Pump_mac_address=Pump_mac_address, Nozzle_address__in=Nozzle_address, Transaction_stop_time__range=transaction_time)

        dates = [x[0] for x in transaction_queryset.values_list(
            'Transaction_stop_time')]
        volumes = []
        amounts = []

        for each in Nozzle_address:
            transaction_queryset = models.TransactionData.objects.filter(
                Site=Site_id, Pump_mac_address=Pump_mac_address, Nozzle_address=each, Transaction_stop_time__range=transaction_time)
            volume = [x[0] for x in transaction_queryset.values_list(
                'Transaction_raw_volume')]
            amount = [x[0] for x in transaction_queryset.values_list(
                'Transaction_raw_amount')]
            volumes.append(volume)
            amounts.append(amount)

        nozzle_names = [
            models.Nozzle.objects.filter(
                Pump__Device__Device_unique_address=Pump_mac_address,
                Pump__id=pump_id,
                Nozzle_address=nozzle,
            ).first().Name
            for nozzle in Nozzle_address
        ]

        trendList = [dates, nozzle_names, volumes, amounts]
        totalVolume = sum(sum(each) for each in volumes)
        totalRevenue = sum(sum(each) for each in amounts)
        data = {'trendList': trendList, 'totalVolume': totalVolume,
                'totalRevenue': totalRevenue}

        return utils.CustomResponse.Success(data)
