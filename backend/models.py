from enum import Enum
from auditlog.registry import auditlog
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.urls import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.core.validators import MinValueValidator, MaxValueValidator

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from .custom_model_fields import EmailListField
from .custom_file_storage import CustomFileStorage
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

class AtgPrimaryLog(models.Model):
    local_id = models.IntegerField(blank=True, null=True)
    multicont_polling_address = models.IntegerField(blank=True, null=True)
    device_address = models.CharField(max_length=50, blank=True, null=True)
    pv = models.CharField(max_length=50, blank=True, null=True)
    pv_flag = models.CharField(max_length=50, blank=True, null=True)
    tank_index = models.IntegerField(blank=True, null=True)
    sv = models.CharField(max_length=50, blank=True, null=True)
    read_at = models.CharField(max_length=50, blank=True, null=True)
    db_fill_time = models.DateTimeField(auto_now_add=True)
    controller_type = models.CharField(max_length=50, blank=True, null=True)
    temperature = models.CharField(max_length=50, blank=True, null=True)
    water = models.CharField(max_length=50, blank=True, null=True)
    tc_volume = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=255, default=None, null=True)
    probe_address = models.CharField(max_length=20, default=None, null=True)
    flag_log = models.BooleanField(default=True, null=False)

    class Meta:
        
        # managed = False
        db_table = 'atg_primary_log'
        # indexes = [models.Index(fields=(
        #     # 'Tank_id',
        #     # 'device_address',
        #     # 'controller_type',
        #     # 'multicont_polling_address',
        #     # 'tank_index'
        #     )
        #     )]
        ordering = ['-read_at']


class Companies(models.Model):

    LOV = (
        ('Multinational', 'Multinational'),
        ('Large', 'Large'),
        ('Medium', 'Medium'),
        ('Small', 'Small')
    )

    Company_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=100)
    Country = models.CharField(max_length=100)
    State = models.CharField(max_length=100)
    City = models.CharField(max_length=100)
    Address = models.CharField(max_length=100)
    Company_type = models.CharField(choices=LOV, max_length=50)
    Company_url = models.CharField(max_length=100, blank=True, null=True)
    Company_image = models.ImageField(
        null=True, blank=True, upload_to='company_avatars', storage=CustomFileStorage())
    Notes = models.TextField(blank=True, null=True)
    Contact_person_name = models.CharField(max_length=100)
    Contact_person_designation = models.CharField(max_length=100, null=True)
    Contact_person_mail = models.CharField(max_length=100, null=True)
    Contact_person_phone = models.CharField(max_length=100, null=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    Active = models.BooleanField(default=True)
    Owned = models.BooleanField(default=False)
    genhours_access = models.BooleanField(default=False)
    smarttank_access = models.BooleanField(default=False)
    smartpump_access = models.BooleanField(default=False)

    def __str__(self):
        return self.Name

    def get_absolute_url(self):
        return reverse('company_list')

    @property
    def number_of_sites(self):
        if self.sites.exists():
            return self.sites.count()
        else:
            return 0


auditlog.register(model=Companies)


class Role(models.Model):
    Role_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)

    def __str__(self):
        return self.Name


auditlog.register(model=Role)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, Email, **extra_fields):

        email = self.normalize_email(Email)
        with transaction.atomic():
            user = self.model(Email=email, **extra_fields)
            password = 'password'
            user.set_password(password)
            user.save(using=self._db)
            return user


class User(AbstractBaseUser):

    status = (
        (1, 'Active'),
        (0, 'Inactive')
    )

    Name = models.CharField(max_length=50)
    Email = models.EmailField(unique=True)
    Phone_number = models.CharField(max_length=25)
    Company = models.ForeignKey(
        Companies, blank=True, null=True, on_delete=models.CASCADE, related_name='users')
    Sites = models.ManyToManyField('Sites', related_name='users', blank=True)
    Role = models.ForeignKey(
        Role, on_delete=models.CASCADE, blank=True, null=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    Status = models.CharField(
        choices=status, default=1, max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    objects = UserManager()

    USERNAME_FIELD = "Email"
    #REQUIRED_FIELD = ["Email","password"]
    REQUIRED_FIELD = ["Email"]
    EMAIL_FIELD = 'Email'

    def __str__(self):
        return self.Name

    def get_absolute_url(self):
        return reverse('user_list')


auditlog.register(model=User, exclude_fields=['password', 'last_login', ])


class Devices(models.Model):
    Device_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Device_unique_address = models.CharField(unique=True, max_length=50)
    Company = models.ForeignKey(
        Companies, on_delete=models.SET_NULL, null=True, blank=True, related_name="devices")
    #Site = models.CharField(max_length=50, blank=True)
    Phone_number = models.CharField(max_length=50, blank=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    transmit_interval = models.PositiveIntegerField(blank=True, default=180)
    Available = models.BooleanField(default=True)
    Active = models.BooleanField(default=False)
    ForPump = models.BooleanField(default=False)
    Used = models.BooleanField(default=False)

    # class Meta:
    #   unique_together = (('Site','Device_unique_address'),)

    def __str__(self):
        return self.Name

    def get_absolute_url(self):
        return reverse('device_list')

    @property
    def get_site(self):
        try:
            site = self.site
        # except Sites.DoesNotExist:
        except:
            site = None
        return site

    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def available(self):
        return not self.get_site

    @property
    @extend_schema_field(OpenApiTypes.OBJECT)
    def adc_sensor_count(self):
        if self.available:  # Device is unavailable i.e connected to a site
            return None
        site = self.get_site
        # get all tanks in site
        tanks = site.tanks_set.filter(Control_mode='S')
        count = 0
        indices = []
        for tank in tanks:
            count += 1
            indices.append(tank.Tank_index)
        return (count, indices)

    @property
    def tank_config_details(self):
        if not self.available:
            site = self.get_site
            tanks = site.tanks_set.filter(Control_mode='C')
            return [{
                'Name': tank.Name,
                'Controller': tank.Tank_controller,
                'Controller_id': tank.Controller_polling_address,
                'Tank_index': tank.Tank_index
            } for tank in tanks]
        return None


auditlog.register(model=Devices)


class Sites(models.Model):
    site_list = (
        ('', 'Choose Site type'),
        ('Industrial', 'Industrial'),
        ('Logistics', 'Logistics'),
        ('Banking', 'Banking'),
        ('Agricultural', 'Agricultural'),
        ('Education', 'Education'),
        ('Hospitality', 'Hospitality'),
        ('Mining', 'Mining'),
        ('Military', 'Military'),
        ('Manufacturing', 'Manufacturing'),
        ('Marine', 'Marine'),
        ('Downstream', 'Downstream'),
        ('Upstream', 'Upstream'),
        ('Aviation', 'Aviation'),
        ('Corporate', 'Corporate'),
        ('Real Estate', 'Real Estate')
    )

    billing_list = (
        ('', 'Number of tanks on site'),
        ('4', '1 to 4 Tanks'),
        ('8', '4 to 8 Tanks'),
        ('16', '8 to 16 Tanks'),
        ('>16', '16+ Tanks')
    )

    Site_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=100)
    Company = models.ForeignKey(
        Companies, on_delete=models.CASCADE, related_name='sites')
    Country = models.CharField(max_length=50)
    State = models.CharField(max_length=100)
    City = models.CharField(max_length=100)
    Address = models.CharField(max_length=100)
    Latitude = models.CharField(max_length=100, blank=True, null=True)
    Longitude = models.CharField(max_length=100, blank=True, null=True)
    Location_status = models.BooleanField(default=False)
    Site_type = models.CharField(choices=site_list, max_length=50)
    Notes = models.TextField(blank=True, null=True)
    Device = models.OneToOneField(
        Devices, on_delete=models.SET_NULL, null=True, blank=True, related_name="site")
    SIM_provided_details = models.CharField(max_length=50, blank=True)
    Number_of_tanks = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)])
    # Tank_count = models.PositiveSmallIntegerField(editable=False, default=0)
    #Next_billing_date = models.DateTimeField(default=None, null=True)
    Reorder_mail = EmailListField(blank=True, default='', null=True)
    Critical_level_mail = EmailListField(blank=True, default='', null=True)
    Contact_person_name = models.CharField(max_length=100, blank=True)
    Contact_person_designation = models.CharField(
        max_length=100, blank=True, null=True)
    Contact_person_mail = models.CharField(
        max_length=100, blank=True, null=True)
    Contact_person_phone = models.CharField(
        max_length=100, blank=True, null=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    Active = models.BooleanField(default=True)
    Communication_status = models.BooleanField(default=True)
    Communication_update_time = models.DateTimeField(blank=True, null=True)
    Email_Notification = models.BooleanField(default=True)
    genhours_access = models.BooleanField(default=False)
    smarttank_access = models.BooleanField(default=False)
    smartpump_access = models.BooleanField(default=False)

    def __str__(self):
        return self.Name

    def get_absolute_url(self):
        return reverse('site_list')

    @property
    @extend_schema_field(OpenApiTypes.INT)
    def tank_count(self):
        if self.tanks.exists():
            return self.tanks.count()
        else:
            return 0

    @property
    def equipment_count(self):
        if self.equipments.exists():
            return self.equipments.count()
        else:
            return 0


auditlog.register(model=Sites)

product_list = (
    ('PMS', 'PMS'),
    ('AGO', 'AGO'),
    ('KERO', 'KERO'),
    ('JET A1', 'JET A1'),
    ('LPFO', 'LPFO'),
    ('SN150', 'SN150'),
    ('BS150', 'BS150'),
    ('SN500', 'SN500'),
    ('USED LUBE', 'USED LUBE'),
    ('LUBE OIL', 'LUBE OIL'),
    ('GEAR OIL', 'GEAR OIL'),
    ('GREASE', 'GREASE'),
    ('WATER', 'WATER'),
    ('GRAIN', 'GRAIN'),
    ('CHEMICALS', 'CHEMICALS')
)


class Products(models.Model):
    Product_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Code = models.CharField(max_length=10)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)

    def __str__(self):
        return self.Name


auditlog.register(model=Products)


measurements = (
    ('L', 'Litres'),
    ('T', 'Tonnes'),
    ('KG', 'Kilogrammes'),
    ('m', 'metres'),
    ('mm', 'millimeters'),
    ('cm', 'centimeters'),
    ('m3', 'cubic-meters'),
    ('gal', 'Gallons')
)

###### SmartPump #######


class PumpBrand(models.Model):
    Name = models.CharField(max_length=255, unique=True)
    OEM = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.Name


auditlog.register(model=PumpBrand)


class Pump(models.Model):
    Name = models.CharField(max_length=255)
    Device = models.ForeignKey(
        Devices, on_delete=models.SET_NULL, related_name="pumps", null=True)
    Site = models.ForeignKey(
        Sites, on_delete=models.CASCADE, related_name="pumps")
    Pumpbrand = models.ForeignKey(
        PumpBrand, on_delete=models.CASCADE, related_name="pumps")
    Pump_protocol = models.CharField(max_length=255)
    Nozzle_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)])
    Note = models.TextField(max_length=255, blank=True, null=True)
    Activate = models.BooleanField(blank=True, default=True)
    Pushed_to_device = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.Name


auditlog.register(Pump)


class Nozzle(models.Model):
    Name = models.CharField(max_length=255)
    Nozzle_address = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)])
    Nozzle_address_hex_code = models.CharField(max_length=255, default='')
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, related_name="nozzle", null=True)
    Pump = models.ForeignKey(
        Pump, on_delete=models.CASCADE, related_name="nozzles")
    Decimal_setting_price_unit = models.IntegerField(
        validators=[MinValueValidator(0)], default=00.0)
    Decimal_setting_amount = models.IntegerField(
        validators=[MinValueValidator(1)])
    Decimal_setting_volume = models.IntegerField(
        validators=[MinValueValidator(1)])
    Totalizer_at_installation = models.IntegerField(
        validators=[MinValueValidator(0)])
    Display_unit = models.CharField(
        choices=measurements, max_length=50, default="L")
    Nominal_flow_rate = models.IntegerField(validators=[MinValueValidator(1)])
    
    def save(self, *args, **kwargs):
        try:
            self.Nozzle_address_hex_code = hex(self.Nozzle_address).replace('x', '')
        except:
            self.Nozzle_address_hex_code = None
        super(Nozzle, self).save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.Name} with id {self.id}'
auditlog.register(Nozzle)


class TransactionData(models.Model):
    Transaction_id = models.BigAutoField(primary_key=True)
    local_id = models.CharField(max_length=255, unique=True)
    Nozzle_address = models.CharField(max_length=255)
    Device = models.ForeignKey(Devices, on_delete=models.CASCADE)
    Site = models.ForeignKey(
        Sites, on_delete=models.CASCADE, related_name='transaction_data')
    Transaction_start_time = models.DateTimeField(auto_now=False, null=True)
    Transaction_stop_time = models.DateTimeField(auto_now=False)
    Transaction_raw_volume = models.FloatField()
    Transaction_raw_amount = models.FloatField()
    Raw_transaction_price_per_unit = models.FloatField()
    Pump_mac_address = models.CharField(max_length=255)
    Transaction_start_pump_totalizer_volume = models.FloatField(null=True)
    Transaction_stop_pump_totalizer_volume = models.FloatField(null=True)
    Transaction_start_pump_totalizer_amount = models.FloatField(null=True)
    Transaction_stop_pump_totalizer_amount = models.FloatField(null=True)
    Product_name = models.CharField(max_length=255, blank=True, null=True)
    Uploaded_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)
    pump_temperature = models.CharField(max_length=255, blank=True, null=True)
    Raw_nozzle_address = models.CharField(max_length=255, default='')


    def save(self, *args, **kwargs):
        try:  # populate the Transaction_product_name using nozzle index,pump address
            product_name_finder = (Nozzle.objects.get(
                Pump__Device__Device_unique_address=self.Pump_mac_address, Nozzle_address=self.Nozzle_address))
            product_name = (product_name_finder.Product.Name)

        except:
            product_name = None

        self.Product_name = product_name
        super(TransactionData, self).save(*args, **kwargs)

    @property
    def pump_name(self):
        try:
            return f'{(Pump.objects.filter(Device__Device_unique_address=self.Pump_mac_address).first()).Name}'
        except:
            pass

    def __str__(self):
        return "Transaction on {0} at site: {1}".format(self.Transaction_stop_pump_totalizer_volume, self.Site.Name)


class PriceChange(models.Model):
    Site = models.ForeignKey(
        Sites, on_delete=models.SET_NULL, related_name='price_change', null=True)
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, related_name='price_change', null=True)
    New_price = models.FloatField()
    mac_address = models.CharField(max_length=255)
    Nozzle_address = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)])
    Note = models.TextField(max_length=255)
    Scheduled_time = models.DateTimeField(auto_now=False)
    Received = models.BooleanField(default=False)
    Approved = models.BooleanField(default=False)
    Rejected = models.BooleanField(default=False)
    TimeImplementedOnDevice = models.DateTimeField(blank=True, null=True)
    ImplementedOnDeviceStatus = models.BooleanField(default=False)


auditlog.register(model=PriceChange)


class RawPriceChangeData(models.Model):
    Site = models.ForeignKey(
        Sites, on_delete=models.SET_NULL, related_name='raw_price_change', null=True)
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, related_name='raw_price_change', null=True)
    New_price = models.FloatField()
    Scheduled_time = models.DateTimeField(auto_now=False)
    Approved = models.BooleanField(default=None, null=True)


auditlog.register(model=RawPriceChangeData)


###### End SmartPump #######


class TankGroups(models.Model):
    Group_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, default=1, blank=True, null=True)
    Company = models.ForeignKey(
        Companies, on_delete=models.CASCADE, related_name='tankgroups')
    UOM = models.CharField(choices=measurements, max_length=50)
    Tanks = models.ManyToManyField('Tanks', blank=True)
    Critical_level_mail = EmailListField(blank=True, null=True, default='')
    Reorder_mail = EmailListField(blank=True, null=True, default='')
    Reorder_Level = models.IntegerField(null=True, blank=True)
    Notes = models.TextField(blank=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    Status = models.BooleanField(default=True)

    @property
    def current_capacity(self):
        if bool(self.Tanks):
            return sum(tank.Capacity for tank in self.Tanks.all())
        else:
            return 0

    @property
    def tank_count(self):
        if bool(self.Tanks):
            return self.Tanks.count()
        else:
            return 0

    @property
    def Alarm_LL_Level(self):
        if bool(self.Tanks):
            return sum(tank.LL_Level for tank in self.Tanks.all())
        else:
            return 0

    @property
    def Alarm_HH_Level(self):
        if bool(self.Tanks):
            return sum(tank.HH_Level for tank in self.Tanks.all())
        else:
            return 0

    def __str__(self):
        return self.Name


auditlog.register(TankGroups)


class Tanks(models.Model):

    shape_list = (
        ('LC', 'Lying Cylindrical'),
        ('SC', 'Standing Cylindrical'),
        ('LR', 'Lying Rectangular'),
        ('SR', 'Standing Rectangular'),
        ('SRV', 'Standard Round View')
    )

    controllers = (
        ('MTC', 'Multicont'),
        ('TLS', 'Veeder'),
        ('SEN', 'Sensor'),
        ('HYD', 'Hydrostatic'),
    )

    Tank_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50, blank=True, null=True)
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, default=1, blank=True, null=True)
    Site = models.ForeignKey(
        Sites, on_delete=models.CASCADE, related_name='tanks')
    Control_mode = models.CharField(max_length=50, default='C')
    Tank_controller = models.CharField(max_length=50, default='MTC')
    Controller_polling_address = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)])
    Tank_index = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(999999)])
    Capacity = models.PositiveIntegerField()
    UOM = models.CharField(choices=measurements, max_length=50, default='L')
    Shape = models.CharField(choices=shape_list, max_length=50, default='LC')
    LL_Level = models.IntegerField(null=True, blank=True, default=0)
    L_Level = models.IntegerField(null=True, blank=True, default=0)
    HH_Level = models.IntegerField(null=True, blank=True, default=0)
    H_Level = models.IntegerField(null=True, blank=True, default=0)
    Reorder = models.IntegerField(null=True, blank=True, default=0)
    Leak = models.IntegerField(null=True, blank=True, default=0)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    Status = models.BooleanField(default=True)
    CalibrationChart = models.FileField(
        null=True, blank=True, upload_to='calibration_charts', storage=CustomFileStorage())
    Offset = models.FloatField(blank=True, null=True, default=0.0)
    Po4 = models.FloatField(blank=True, null=True, default=0.0)
    Display_unit = models.CharField(
        choices=measurements, max_length=50, blank=True, default='L')
    Density = models.FloatField(null=True, default=None)
    Tank_height = models.FloatField(null=True, default=None)
    Anomaly_period = models.FloatField(null=True, default=None)
    Anomaly_volume = models.FloatField(null=True, default=None)
    Tank_Note=models.CharField(max_length=25,blank=True, null=True)

    def __str__(self):
        #return self.Name
        return f'Tank:{self.Name},Site:{self.Site.Name},Company:{self.Site.Company.Name}'
auditlog.register(model=Tanks)


class PasswordReset(models.Model):
    '''
    INITIAL_STATUS = 0
    CONFIRMED_STATUS = 1

    Password_reset_status = (
        (INITIAL_STATUS, 'unconfirmed'),
        (CONFIRMED_STATUS, 'confirmed'),
        )
    '''
    user_id = models.PositiveIntegerField()
    token = models.CharField(max_length=100)
    confirmation_status = models.BooleanField(default=False)
    reset_request_time = models.DateTimeField(auto_now_add=True)
# Don't log password reset coz the auditlog api will expose the tokens for password reset


class Version(models.Model):
    Version_id = models.AutoField(primary_key=True)
    Version_number = models.CharField(max_length=50, unique=True)
    Download_link = models.TextField()
    Filename = models.CharField(max_length=50)
    Created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.Version_number


auditlog.register(model=Version)


class Deliveries(models.Model):
    volume = models.CharField(max_length=50, blank=True, null=True)
    local_id = models.IntegerField(blank=True, null=True)
    tc_volume = models.CharField(max_length=50, blank=True, null=True)
    db_fill_time = models.DateTimeField(blank=True, null=True)
    system_start_time = models.DateTimeField(blank=True, null=True)
    system_end_time = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    polling_address = models.CharField(max_length=50, blank=True, null=True)
    tank_index = models.CharField(max_length=50, blank=True, null=True)
    device_address = models.CharField(max_length=50, blank=True, null=True)
    controller_type = models.CharField(max_length=50, blank=True, null=True)
    end_volume = models.CharField(max_length=50, blank=True, null=True)
    start_volume = models.CharField(max_length=50, blank=True, null=True)
    start_height = models.CharField(max_length=50, blank=True, null=True)
    end_height = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        #managed = False
        db_table = 'deliveries'


class DeviceFirmwareVersion(models.Model):
    device_mac_address = models.CharField(
        max_length=100, blank=True, null=True)
    version_number = models.CharField(max_length=100, blank=True, null=True)
    expected_version_number = models.CharField(
        max_length=200, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    device = models.ForeignKey(
        Devices, on_delete=models.SET_NULL, null=True, blank=True, related_name='firmware')

    class Meta:
        #managed = False
        db_table = 'device_firmware_version'

    def save(self, *args, **kwargs):
        # only save (either create or update)
        # if the device_mac_address is a valid device,
        # then set the device_id FK
        try:
            dev = Devices.objects.get(
                Device_unique_address=self.device_mac_address)
        except Devices.DoesNotExist:
            dev = None

        if dev is not None:
            self.device = dev
            super(DeviceFirmwareVersion, self).save(*args, **kwargs)


class Probes(models.Model):
    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=50)
    probe_chart = models.FileField(
        null=True, blank=True, upload_to='probe_charts/', storage=CustomFileStorage())

    def __str__(self):
        return self.slug


auditlog.register(model=Probes)


class TankAlarmDispatcher(models.Model):
    tank_id = models.IntegerField()
    alarm_type = models.CharField(max_length=45, blank=True, null=True)
    last_time_mail_sent = models.DateTimeField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'tank_alarm_dispatcher'


class GeneratorHours(models.Model):
    mac_address = models.CharField(max_length=50)
    lineID = models.IntegerField()
    status = models.IntegerField()
    timestamp = models.DateTimeField()
    db_fill_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}-{}".format(self.mac_address, self.lineID)

    class Meta:
        indexes = [models.Index(fields=(
            'mac_address',
            'lineID'))]


class FlowmeterLogs(models.Model):
    uid = models.CharField(max_length=50, default=None)
    mac_address = models.CharField(max_length=50)
    flowmeter_address = models.IntegerField()
    litres = models.FloatField()
    hours = models.FloatField()
    forward_litres = models.FloatField()
    backward_litres = models.FloatField()
    forward_fuel_rate = models.FloatField()
    backward_fuel_rate = models.FloatField()
    consumption_rate = models.FloatField()
    temperature = models.FloatField()
    status = models.IntegerField()
    mode = models.CharField(max_length=50)
    timestamp = models.DateTimeField()
    db_fill_time = models.DateTimeField(auto_now_add=True)
    flowmeter_serial_number = models.CharField(
        max_length=50, blank=True, default="Test")

    def __str__(self):
        return "{}-{}".format(self.mac_address, self.flowmeter_address)

    class Meta:
        indexes = [models.Index(fields=(
            'mac_address',
            'flowmeter_address'))]


class Equipment(models.Model):
    equipment_types = (
        ('GEN', 'Generator'),
        ('BLR', 'Boiler'),
        ('VEH', 'Vehicle')
    )

    hours_sources = (
        ('FM', 'Flowmeter'),
        ('DI', 'Direct Integration'),
        ('HYB-FM', 'FM + DI(FM Primary)'),
        ('HYB-DI', 'FM + DI(DI Primary)')
    )

    litres_sources = (
        ('TL', 'Tank Levels'),
        ('FM', 'Flowmeter'),
        ('HYB-TL', 'TL + FM(TL Primary)'),
        ('HYB-FM', 'TL + FM(FM Primary)')
    )

    name = models.CharField(max_length=50)
    product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, default=1, blank=True, null=True)
    equipment_type = models.CharField(
        choices=equipment_types, max_length=20, default='GEN')
    oem = models.CharField(max_length=200)
    model = models.CharField(max_length=200)
    oem_consumption_rate = models.FloatField(blank=True, null=True)
    nominal_consumption_rate = models.FloatField(blank=True, null=True)
    max_consumption_rate = models.FloatField(blank=True, null=True)
    min_consumption_rate = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True)
    initial_totaliser_hours = models.PositiveIntegerField(
        blank=True, default=0)
    totaliser_hours = models.FloatField(blank=True, null=True)
    totaliser_litres = models.FloatField(blank=True, null=True, default=0)
    last_genhours_calculated_time = models.DateTimeField(null=True, blank=True)
    site = models.ForeignKey(
        Sites, on_delete=models.CASCADE, related_name='equipments')
    running_hours_source = models.CharField(
        choices=hours_sources, max_length=20)
    litres_consumed_source = models.CharField(
        choices=litres_sources, max_length=20)
    flowmeter = models.OneToOneField(
        'Flowmeter', on_delete=models.SET_NULL, blank=True, null=True, related_name='equipment')
    address = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)], blank=True, null=True)
    source_tanks = models.ManyToManyField(Tanks, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    gen_phase = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)],
                                            blank=True, null=True)

    def __str__(self):
        return self.name

    # Add a pre-create hook logic to populate total_genhours with initial_genhours if set
    def save(self, *args, **kwargs):
        if not self.pk:  # Initial save(create), no primary key generated yet
            super(Equipment, self).save(*args, **kwargs)
            self.totaliser_hours = self.initial_totaliser_hours
            self.save()
        else:  # update save
            super(Equipment, self).save(*args, **kwargs)

    @property
    def tank_connection_status(self):
        return self.litres_consumed_source != 'TL' or self.source_tanks.count() != 0


auditlog.register(model=Equipment)


class Flowmeter(models.Model):
    meter_types = (
        ('DFM', 'DFM Modbus'),
        ('PUL', 'Pulser')
    )

    serial_number = models.CharField(max_length=200, unique=True)
    site = models.ForeignKey(Sites, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='flowmeters')
    max_temp = models.FloatField(blank=True, null=True)
    meter_type = models.CharField(
        choices=meter_types, max_length=50, default='DFM')
    address = models.PositiveIntegerField()
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.serial_number

    @property
    def get_connected_equipment(self):
        try:
            equipment = self.equipment
        except Equipment.DoesNotExist:
            equipment = None
        return equipment

    @property
    def available(self):
        return not self.get_connected_equipment


auditlog.register(model=Flowmeter)


class PowerMeter(models.Model):
    meter_types = (
        ('DPP', 'Digital Power Probe'),
        ('DPM', 'Digital Power Meter'),
    )

    serial_number = models.CharField(
        max_length=200, unique=True, help_text="Mapping each Power Meter")
    site = models.ForeignKey(Sites, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='powermeters')
    meter_type = models.CharField(
        choices=meter_types, max_length=50, default='DPP')
    address = models.PositiveIntegerField()
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='powermeter')

    def __str__(self):
        return self.serial_number


auditlog.register(model=PowerMeter)


class PowermeterLogs(models.Model):
    uid = models.CharField(max_length=50, default=None)
    mac_address = models.CharField(max_length=50, db_index=True)
    powermeter_address = models.IntegerField()
    voltage_a = models.FloatField(blank=True, null=True)
    voltage_b = models.FloatField(blank=True, null=True)
    voltage_c = models.FloatField(blank=True, null=True)
    current_a = models.FloatField(blank=True, null=True)
    current_b = models.FloatField(blank=True, null=True)
    current_c = models.FloatField(blank=True, null=True)
    power_a = models.FloatField(blank=True, null=True)
    power_b = models.FloatField(blank=True, null=True)
    power_c = models.FloatField(blank=True, null=True)
    power_total = models.FloatField(blank=True, null=True)
    frequency = models.FloatField(blank=True, null=True)
    power_factor = models.FloatField(blank=True, null=True)
    active_energy = models.FloatField(blank=True, null=True)
    status = models.IntegerField(default=0)
    timestamp = models.DateTimeField(db_index=True)
    engine_running = models.IntegerField(blank=True, null=True)
    db_fill_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='powermeterlogs')

    def __str__(self):
        return "{}-{}".format(self.mac_address, self.powermeter_address)


class MaintenanceConfig(models.Model):
    modes = (
        ('HR/D', 'Hours/Days'),
        ('SCH', 'Schedule(Days)')
    )
    equipment = models.OneToOneField(
        Equipment, on_delete=models.CASCADE, related_name='maintenance_config')
    mode = models.CharField(choices=modes, max_length=50)
    hours = models.IntegerField(null=True)
    days = models.IntegerField(null=True)
    scheduled_days = models.IntegerField(null=True)

    def __str__(self):
        return "Equipment-Maintenance-{}".format(self.equipment)


class MaintenanceInfo(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='maintenance_infos')
    maintenance_date = models.DateField()
    notes = models.TextField(blank=True)
    genhours = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


def get_image_filename(instance, filename):
    equipment_id = instance.maintenance_info.equipment.pk
    date = instance.maintenance_info.maintenance_date
    return "maintenance_images/equipment_{}/{}/{}".format(equipment_id, date, filename)


class MaintenanceInfoImage(models.Model):
    maintenance_info = models.ForeignKey(
        MaintenanceInfo, on_delete=models.CASCADE, related_name='info_images')
    image = models.ImageField(
        upload_to=get_image_filename, storage=CustomFileStorage())


class FlowmeterTransactionComment(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='equipment_transaction_comments')
    trx_end_time = models.CharField(max_length=50)
    comment = models.TextField(blank=True)
    comment_create_author = models.CharField(max_length=50)
    comment_create_time = models.DateTimeField(auto_now_add=True)
    comment_edit_author = models.CharField(max_length=50, blank=True)
    comment_edit_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Equipment-{}: {}".format(self.equipment, self.trx_end_time)


class SiteGenHoursConfiguration(models.Model):
    site = models.OneToOneField(
        Sites, on_delete=models.CASCADE, related_name="genhours_config")
    monitor_public_power = models.BooleanField(default=False)
    public_power_source_slug = models.CharField(
        default="PHCN Source", max_length=50)

    def __str__(self):
        return "Config:Site {}".format(self.site)

###########Site Groups#############


class SiteGroups(models.Model):
    Name = models.CharField(max_length=50)
    Company = models.ForeignKey(
        Companies, on_delete=models.CASCADE, related_name='sitegroups')
    Sites = models.ManyToManyField('Sites', blank=True)
    Active = models.BooleanField(default=True)


class ProductPriceHistory(models.Model):
    Company = models.ForeignKey(
        Companies, on_delete=models.SET_NULL, related_name='product_price_history', null=True)
    Site = models.ForeignKey(
        Sites, on_delete=models.SET_NULL, related_name='product_price', null=True, blank=True)
    Price = models.FloatField()
    Sheduled_time = models.DateTimeField(auto_now=False)
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, null=True)
    Approved_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, related_name="product_price_history", null=True)
    Initial = models.BooleanField(default=False)
    Reference_code = models.CharField(max_length=100, blank=True, null=True)
    db_fill_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)


auditlog.register(model=ProductPriceHistory)


class PriceChangeRequestData(models.Model):

    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, related_name='raw_price_change_request', null=True)
    New_price = models.FloatField()
    Scheduled_time = models.DateTimeField(auto_now=False)
    Approved = models.BooleanField(default=None, null=True)
    Company = models.ForeignKey(
        Companies, on_delete=models.SET_NULL, related_name='raw_price_change_request', null=True)
    Site = models.ForeignKey(
        Sites, on_delete=models.SET_NULL, related_name='raw_product_price_request', null=True, blank=True)
    Initiator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="raw_price_change_request_initiator", null=True)
    Actor = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="raw_price_change_request_actor", null=True)
    Rejection_note = models.CharField(max_length=200, blank=True, null=True)
    Approval_or_rejection_time = models.DateTimeField(
        auto_now=False, blank=True, null=True)
    db_fill_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)

auditlog.register(model=PriceChangeRequestData)


class CompanyProductPriceRequest(models.Model):
    '''A single place to change price of product accross all sites in a company'''
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, related_name='company_product_price_change_request', null=True)
    New_price = models.FloatField()
    Scheduled_time = models.DateTimeField(auto_now=False)
    Approved = models.BooleanField(default=None, null=True)
    Company = models.ForeignKey(
        Companies, on_delete=models.SET_NULL, related_name='product_price_change_request', null=True)
    Initiator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="company_product_price_change_request_initiator", null=True)
    Actor = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="company_product_price_change_request_actor", null=True)
    Rejection_note = models.CharField(max_length=200, blank=True, null=True)
    Approval_or_rejection_time = models.DateTimeField(
        auto_now=False, blank=True, null=True)
    db_fill_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)


auditlog.register(model=CompanyProductPriceRequest)


class DevicePriceExecution(models.Model):
    ''' Logs to keep track of price execution on the device '''
    Site = models.ForeignKey(
        Sites, on_delete=models.SET_NULL, related_name='executed_prices', null=True)
    Company = models.ForeignKey(
        Companies, on_delete=models.SET_NULL, related_name='executed_prices', null=True)
    Time_executed = models.DateTimeField(auto_now=False)
    Price = models.FloatField()
    Product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, related_name='executed_prices', null=True)
    Execution_status = models.BooleanField(default=False)
    Pump_reference = models.CharField(max_length=255)


class PumpDeviceHeartbeats(models.Model):
    local_ip = models.CharField(max_length=50, blank=True, null=True)
    device_mac_address = models.CharField(
        max_length=100, blank=True, null=True)
    last_time_online = models.DateTimeField(blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    last_transaction_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'pump_device_heartbeats'
        

########Company Groups#############


class CompanyGroups(models.Model):
    Group_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=100, unique=True)
    Companies = models.ManyToManyField(
        'Companies', related_name='group', blank=True)
    Status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    Notes = models.TextField(blank=True, null=True)

auditlog.register(model=CompanyGroups)


class Modules(models.Model):
    module_id = models.AutoField(primary_key=True)
    module_name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)


class UserAccessPermissions(models.Model):
    permission_name = models.CharField(max_length=20, unique=True)
    read = models.BooleanField(default=False)
    create =  models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    module = models.ForeignKey(Modules,on_delete=models.SET_NULL, null=True)


class NewUserRole(models.Model):
    Role_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    role_permission = models.ManyToManyField(UserAccessPermissions,related_name='permissionroles', blank=True)
    active = models.BooleanField(default=True)

    #[*] Superadmin and Product Admin UserRole are default roles for Users

class NewUser(AbstractBaseUser):

    status = (
        (1, 'Active'),
        (0, 'Inactive')
    )

    Name = models.CharField(max_length=50)
    Email = models.EmailField(unique=True)
    Phone_number = models.CharField(max_length=25)
    NewCompany = models.ForeignKey(
        Companies, blank=True, null=True, on_delete=models.CASCADE, related_name='userscompany')
    Sites = models.ManyToManyField('Sites', related_name='userssites', blank=True)
    Role = models.ForeignKey(
        NewUserRole, on_delete=models.CASCADE, blank=True, null=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)
    Deleted_at = models.DateTimeField(default=None, null=True)
    Status = models.CharField(
        choices=status, default=1, max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    objects = UserManager()

    USERNAME_FIELD = "Email"
    REQUIRED_FIELD = ["Email"]
    EMAIL_FIELD = 'Email'

    def __str__(self):
        return self.Name

class UserProfile(models.Model):
    sex = (
        ('Male', 'Male'),
        ('Female', 'Female')
    )
    user = models.OneToOneField(
        NewUser, on_delete=models.SET_NULL, null=True, blank=True)
    birth_date = models.DateField()
    sex = models.CharField(choices=sex, max_length=50)
    

class LatestAtgLog(models.Model):
    Tank_id = models.IntegerField(unique=True)
    Tank_name= models.CharField(max_length=50, blank=True, null=True)
    Volume = models.FloatField(blank=True, null=True)
    Height = models.CharField(max_length=10, blank=True, null=True)
    temperature = models.CharField(max_length=10, blank=True, null=True)
    water = models.CharField(max_length=10, blank=True, null=True)
    db_updated_time = models.DateTimeField(auto_now=True, null=True, blank=True)
    last_updated_time = models.DateTimeField(null=True, blank=True)
    Site_id = models.IntegerField(blank=True, null=True)
    siteName = models.CharField(max_length=100)
    Capacity =   models.PositiveIntegerField()
    Unit  = models.CharField(max_length=50, blank=True, null=True)
    DisplayUnit = models.CharField(max_length=50, blank=True, null=True)
    Product = models.CharField(max_length=50, blank=True, null=True)
    Fill = models.FloatField(null=True, default=None)
    Tank_controller = models.CharField(max_length=50, default='MTC')
    Reorder = models.IntegerField(null=True, blank=True, default=0)
    LL_Level = models.IntegerField(null=True, blank=True, default=0)
    HH_Level = models.IntegerField(null=True, blank=True, default=0)
    Tank_Status = models.BooleanField(default=True)
    Tank_Note=models.CharField(max_length=25,blank=True, null=True)
    


    class Meta:

        indexes = [models.Index(fields=(
            # 'Tank_id',
            'Site_id',
            ))]

class UniqueAddressTracker(models.Model):
    address = models.CharField(max_length=250,unique=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SF-{self.id}"
auditlog.register(model=UniqueAddressTracker, exclude_fields=['address'])

class SmartSolarData(models.Model):
    mac_address = models.CharField(max_length=250, blank=True, null=True,)
    energy_time_log = models.CharField(max_length=250, blank=True, null=True,)
    inv_time_log = models.CharField(max_length=250, blank=True, null=True,)
    battery_voltage = models.CharField(max_length=250, blank=True, null=True)
    solar_voltage = models.CharField(max_length=250, blank=True, null=True)
    grid_voltage = models.CharField(max_length=250, blank=True, null=True)
    output = models.CharField(max_length=250, blank=True, null=True)
    previous_day_solar_unit = models.CharField(max_length=250, blank=True, null=True)
    solar_status = models.CharField(max_length=250, blank=True, null=True)
    today_total_solar = models.CharField(max_length=250, blank=True, null=True)
    today_solar_consume_for_charging = models.CharField(max_length=250, blank=True, null=True)
    solar_current = models.CharField(max_length=250, blank=True, null=True)
    grid_state = models.CharField(max_length=250, blank=True, null=True)
    today_solar_consume_for_load = models.CharField(max_length=250, blank=True, null=True)
    total_charging_current = models.CharField(max_length=250, blank=True, null=True)
    today_battery_consume_for_load = models.CharField(max_length=250, blank=True, null=True)
    discharging_current = models.CharField(max_length=250, blank=True, null=True)
    today_grid_consume_for_charging = models.CharField(max_length=250, blank=True, null=True)
    today_load_on_grid = models.CharField(max_length=250, blank=True, null=True)
    instantaneous_solar_power = models.CharField(max_length=250, blank=True, null=True)
    load_on = models.CharField(max_length=250, blank=True, null=True)
    output_voltage = models.CharField(max_length=250, blank=True, null=True)
    output_current = models.CharField(max_length=250, blank=True, null=True)
    output_power = models.CharField(max_length=250, blank=True, null=True)
    output_energy = models.CharField(max_length=250, blank=True, null=True)
    device_type = models.CharField(max_length=250, blank=True, null=True)
    location = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f"{self.id}"
    class Meta:
        app_label = 'backend'

class TankLogAnomaly(models.Model):
    company_name = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='companies')
    site_name = models.ForeignKey(Sites, on_delete=models.CASCADE, related_name='sites')
    tank_name = models.ForeignKey(Tanks, on_delete=models.CASCADE, related_name='tank_index')
    anomaly_period = models.CharField(max_length=100, blank=True, null=True)
    anomaly_difference = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        app_label = 'backend'
# auditlog.register(model=TankLogAnomaly)

# class DailyMissedLog(models.Model):
#     Tank_id = models.IntegerField()
#     Tank_name = models.CharField(max_length=50, blank=True, null=True)
#     Product_name=models.CharField(max_length=255, blank=True, null=True)
#     Company_id = models.IntegerField()
#     Company_name = models.CharField(max_length=100)
#     Site_id = models.IntegerField()
#     Site_name = models.CharField(max_length=100)
#     Log_date = models.DateField()
#     Db_fill_time = models.DateTimeField(auto_now_add=True)
#     Status = models.CharField(max_length=100,blank=True, null=True)
#     Missed_interval = models.TextField(blank=True, null=True)

