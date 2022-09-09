from django.db.models.signals import post_save
from django.dispatch import receiver
# from .sites.serializer import Sites
from backend import models
from django.utils import timezone
import datetime
# @receiver(post_save, sender=SiteSerializer)
# def updateDeviceSite(sender, instance, **kwargs):
#     device = models.Devices.objects.get(pk=instance['Device'].Device_id)
#     device.Site = instance['Name']
#     device.Available = False
#     device.save()

@receiver(post_save, sender=models.UniqueAddressTracker)
def update_device_address(sender, instance, created, **kwargs):
    if created:
        date = datetime.datetime.strftime(instance.date_created, '%Y%m%d')
        instance.address = f"SF-{date}-{instance.id}"
        instance.save() 


@receiver(post_save, sender=models.Tanks)
def create_latest_atg_log_instance(sender, instance, created, **kwargs):
    print(instance, 'instance--------')
    obj, created = models.LatestAtgLog.objects.update_or_create(Tank_id=instance.Tank_id,
    Site_id=instance.Site.Site_id, defaults={'Capacity': instance.Capacity, 'Unit': instance.UOM,
     'DisplayUnit': instance.Display_unit,'Product': instance.Product.Name, 'Tank_name': instance.Name, 
     'siteName': instance.Site.Name, 'Tank_controller': instance.Tank_controller,
     'Reorder': instance.Reorder, 'LL_Level': instance.LL_Level, 'HH_Level': instance.HH_Level,
     'Tank_Status':instance.Status,'Tank_Note':instance.Tank_Note}
    )
