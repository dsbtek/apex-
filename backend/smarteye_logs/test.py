from unittest import mock

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models

class LogsModelTests(APITestCase):
    def test_logs_bulk_create(self):
        logs = [models.AtgPrimaryLog(local_id=123, multicont_polling_address=1, 
        device_address='abcde', pv='123.45', pv_flag='1',
        tank_index=1, sv='220', read_at='2020-03-19 17:45', controller_type='MTC') for _ in range(10)]

        models.AtgPrimaryLog.objects.bulk_create(logs)
        self.assertEqual(models.AtgPrimaryLog.objects.count(), 10)


class DataLoggerTest(APITestCase):
    @mock.patch('backend.smarteye_logs.views.tank_alarm_task')
    def test_data_logger(self, mock_task):
        device_logs = [(54563, '2019-04-30 20:50:13', '16733.099609375', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54561, '2019-04-30 20:50:08', '33.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                    (54562, '2019-04-30 20:50:08', '928.400024414063', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                    (54560, '2019-04-30 20:48:14', '16742.69921875', '1', '152.199996948242', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54558, '2019-04-30 20:48:08', '33.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                    (54559, '2019-04-30 20:48:08', '928.5', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                    (54557, '2019-04-30 20:46:14', '16734.0', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54555, '2019-04-30 20:46:08', '33.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                    (54556, '2019-04-30 20:46:08', '928.5', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                    (54554, '2019-04-30 20:44:13', '16736.80078125', '1', '152.199996948242', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54553, '2019-04-30 20:44:08', '928.5', '3', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                    (54552, '2019-04-30 20:44:07', '33.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                    (54551, '2019-04-30 20:42:13', '16731.19921875', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54550, '2019-04-30 20:42:08', '843.599975585938', '2', '249.199996948242', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                    (54549, '2019-04-30 20:42:07', '33.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                    (54548, '2019-04-30 20:40:13', '16732.19921875', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54547, '2019-04-30 20:40:08', '928.5', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                    (54546, '2019-04-30 20:40:07', '33.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                    (54545, '2019-04-30 20:38:13', '16731.0', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                    (54544, '2019-04-30 20:38:08', '928.200012207031', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC')
                    ]
        url = reverse('data_logger')
        mock_task.delay.side_effect = print('Sent to celery task!!!')
        response = self.client.post(url, data=device_logs, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.delay.assert_called_once()


class SensorDataLoggerTest(APITestCase):
    @mock.patch('backend.smarteye_logs.views.analog_probe_logger')
    def test_analog_probe_logger(self, mock_task):
        sensor_logs = [(1,1,1,'4.587','1.10','b8:27:eb:97:8c:12','SEN','2020-10-01 13:56'),
                        (2,1,1,'4.902','1.20','b8:27:eb:97:8c:12','SEN','2020-10-01 14:00'),
                        (3,1,1,'5.20','1.60','b8:27:eb:97:8c:12','SEN','2020-10-01 14:06')]
        url = reverse('sensor_data_logger')
        mock_task.delay.side_effect = print('Sent to celery task!')
        response = self.client.post(url, data=sensor_logs, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # mock_task.delay.assert_called_once()

class TLSDeliveryLoggerTest(APITestCase):
    def test_tls_delivery_logger(self):
        logs = [(10,'2020-10-01 13:56','b8:27:eb:97:8c:12',1,1,'30000','30010', '2020-10-01T10:56','2020-10-01T13:56','100', '120.4', '12000', '42000', 'TLS')]
        url = reverse('tls_delivery_logger')
        response = self.client.post(url, data=logs, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.Deliveries.objects.count(), 1)
