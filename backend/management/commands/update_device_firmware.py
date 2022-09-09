from django.core.management.base import BaseCommand

from backend import models


class Command(BaseCommand):
    help = 'Set device fk for firmware objects'

    def handle(self, *args, **kwargs):
        firmware_entries = models.DeviceFirmwareVersion.objects.all()
        self.stdout.write(self.style.NOTICE("Total device firmware entries: {}".format(firmware_entries.count())))
        count = 0
        for entry in firmware_entries:
            self.stdout.write(self.style.SUCCESS(entry))
            try:
                device = models.Devices.objects.get(Device_unique_address=entry.device_mac_address)
            except models.Devices.DoesNotExist:
                continue
            entry.device = device
            entry.save()
            count += 1
        
        self.stdout.write(self.style.NOTICE("Total firmware updates: {}".format(count)))
