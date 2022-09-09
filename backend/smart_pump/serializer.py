
from rest_framework import serializers
from backend import models
from auditlog.models import LogEntry


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Devices
        fields = "__all__"


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sites
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Products
        fields = "__all__"


class TransactionRequestDataSerializer(serializers.ModelSerializer):
    Site = SiteSerializer()

    class Meta:
        model = models.TransactionData
        fields = "__all__"


class TransactionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TransactionData
        fields = "__all__"



class TransactionDataResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TransactionData
        # fields = "__all__"
        fields = ('Nozzle_address','Transaction_start_time','Transaction_stop_time','Transaction_raw_volume',
        'Transaction_raw_amount','Raw_transaction_price_per_unit','Pump_mac_address','Product_name')

class PumpBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PumpBrand
        fields = "__all__"


class PumpSaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Pump
        fields = "__all__"


class NozzleSaveSerializer(serializers.ModelSerializer):
    Pump_mac_name = serializers.SerializerMethodField()
    Price = serializers.SerializerMethodField()
    Product_name = serializers.CharField(source="Product.Name", read_only=True)
    Price_time = serializers.SerializerMethodField()
    First_initial_price = serializers.SerializerMethodField()

    class Meta:
        model = models.Nozzle
        fields = "__all__"

    def get_Pump_mac_name(self, obj):
        try:
            return obj.Pump.Device.Device_unique_address
        except :
            return None
        

    def get_First_initial_price(self, obj):
        try:
            product_price = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()).Price
        except AttributeError:
            product_price = None

        return product_price

    def get_Price(self, obj):
        try:
            product_price = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()).Price
        except AttributeError:
            product_price = None

        return product_price

    def get_Price_time(self, obj):
        try:
            price_time = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()). Sheduled_time
        except AttributeError:
            price_time = None
        return price_time


class PumpSerializer(serializers.ModelSerializer):
    Device = DeviceSerializer()
    Site = SiteSerializer()
    Pumpbrand = PumpBrandSerializer()
    nozzles = NozzleSaveSerializer(many=True, read_only=True)

    class Meta:
        model = models.Pump
        fields = "__all__"

class PicNozzleSerializer(serializers.ModelSerializer):
    Price = serializers.SerializerMethodField()
    Price_time = serializers.SerializerMethodField()
    Nozzle_count = serializers.IntegerField(source='Pump.Nozzle_count', read_only=True)
    Pump_protocol = serializers.CharField(source='Pump.Pump_protocol', read_only=True)
    Device_id = serializers.IntegerField(source='Pump.Device.Device_id', read_only=True)
    Site_id = serializers.IntegerField(source='Pump.Site.Site_id', read_only=True)

    class Meta:
        model = models.Nozzle
        fields = ('Site_id','Device_id','Nozzle_count','Pump_protocol','Nozzle_address', 'Nozzle_address_hex_code','Price','Price_time','Decimal_setting_price_unit','Decimal_setting_amount','Decimal_setting_volume')

  

    def get_Price(self, obj):
        try:
            product_price = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()).Price
        except AttributeError:
            product_price = None

        return product_price

    def get_Price_time(self, obj):
        try:
            price_time = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()). Sheduled_time
        except AttributeError:
            price_time = None
        return price_time


class NozzleSerializer(serializers.ModelSerializer):
    First_initial_price = serializers.SerializerMethodField()
    Price = serializers.SerializerMethodField()
    Price_time = serializers.SerializerMethodField()
    Pump = PumpSerializer()
    Product = ProductSerializer()

    class Meta:
        model = models.Nozzle
        fields = "__all__"

    def get_First_initial_price(self, obj):
        try:
            product_price = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()).Price
        except AttributeError:
            product_price = None

        return product_price

    def get_Price(self, obj):
        try:
            product_price = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()).Price
        except AttributeError:
            product_price = None

        return product_price

    def get_Price_time(self, obj):
        try:
            price_time = (models.ProductPriceHistory.objects.filter(
                Product=obj.Product.Product_id, Company=obj.Pump.Device.Company, Site=obj.Pump.Site).last()). Sheduled_time
        except AttributeError:
            price_time = None
        return price_time


class PriceChangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PriceChange
        fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Companies
        fields = "__all__"


class RawPriceChangeDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RawPriceChangeData
        fields = "__all__"


class DevicePriceExecutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.DevicePriceExecution
        fields = "__all__"


class PriceChangeRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PriceChangeRequestData
        fields = "__all__"


class CompanyProductPriceChangeRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CompanyProductPriceRequest
        fields = "__all__"


class GetPriceRequestDataSerializer(serializers.ModelSerializer):
    Product = ProductSerializer()
    Initiator = serializers.StringRelatedField(many=False)
    Actor = serializers.StringRelatedField(many=False)
    Company_name = serializers.CharField(source="Company.Name", read_only=True)
    Site_name = serializers.CharField(source="Site.Name", read_only=True)

    class Meta:
        model = models.PriceChangeRequestData
        fields = "__all__"


class GetCompanyPriceRequestDataSerializer(serializers.ModelSerializer):
    Product = ProductSerializer()
    Initiator = serializers.StringRelatedField(many=False)
    Actor = serializers.StringRelatedField(many=False)
    Company_name = serializers.CharField(source="Company.Name", read_only=True)

    class Meta:
        model = models.CompanyProductPriceRequest
        fields = "__all__"


class GetRawPriceChangeDataSerializer(serializers.ModelSerializer):
    Site = SiteSerializer()
    Product = ProductSerializer()

    class Meta:
        model = models.RawPriceChangeData
        fields = "__all__"


class RequestParamsSerializer(serializers.Serializer):
    Site_id = serializers.IntegerField()
    Start_time = serializers.DateField()
    End_time = serializers.DateField()
    Products = serializers.CharField()


class TransactionDataWithPumpNameSerializer(serializers.ModelSerializer):
    Pump_name = serializers.SerializerMethodField()

    class Meta:
        model = models.TransactionData
        fields = "__all__"

    def get_Pump_name(self, obj):
        return obj.pump_name
