import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

from ..reports.custom_reports import extract_all_tanks_details, get_logs_within_range, delivery_report
from backend import models
from .serializers import TankSiteSerializer
from .. import utils


class APIKEYGenerator():

	def key_generator(self):
	    text = b'API_KEY'
	    salt = b'Energy360Africa' # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes

	    kdf = PBKDF2HMAC(
	        algorithm=hashes.SHA256(),
	        length=32,
	        salt=salt,
	        iterations=100000,
	        backend=default_backend()
	    )
	    return base64.urlsafe_b64encode(kdf.derive(text)) # Can only use kdf once

	def generate_encrypted_token(self,key, station_id):
	    f = Fernet(key)
	    encrypted_token = f.encrypt(str(station_id).encode())
	    return encrypted_token.decode('utf-8')

	def check_and_extract_id_from_token(self,key, token):
	    token = token.encode()
	    fg = Fernet(key)
	    station_id = fg.decrypt(token)
	    station_id = int(station_id.decode())
	    return station_id


def check_token(request_dict):
	api_key = request_dict.get('HTTP_API_KEY', None)
	payload = {'id':None, 'invalid': False}
	if api_key:
		try:
			keygen = APIKEYGenerator()
			key = keygen.key_generator()
			station_id = keygen.check_and_extract_id_from_token(key, api_key)
			payload['id'] = station_id
		except InvalidToken:
			payload['invalid'] = True

	return payload
	 
		
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def request_middleware(request):
	payload = check_token(request.META)
	valid_token = payload.get('invalid')
	station_id = payload.get('id')

	return valid_token, station_id


def get_tanks_in_a_site(site_id):
	queryset = models.Tanks.objects.filter(Site__Site_id=site_id)
	serializer = TankSiteSerializer(queryset, many=True)
	tank_ids = []
	for data in serializer.data:
		tank_ids.append(data['Tank_id'])

	return tank_ids 

def delivery_report_generator(start, end, station_id, tank_name):
	tank_id = [models.Tanks.objects.get(Site_id=station_id, Name=tank_name).Tank_id]

	details = extract_all_tanks_details(tank_id)
	stock_log = get_logs_within_range(start, end, details[0])
	report = delivery_report(stock_log, details[0])
	return report