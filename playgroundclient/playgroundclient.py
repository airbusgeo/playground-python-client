import json
import requests
import time
import math
import os.path

class NetException(Exception):
    """Tile Exception: generic error for Internet"""
    def __init__(self, message):
        """Tile Exception contructor"""
        super(NetException, self).__init__(message)

class PlaygroundClientError(Exception):
    """Exception raised for errors in the Playground Client.

    Attributes:
        status_code -- status code of the error occurred
        message -- explanation of the error
    """

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

class PlaygroundClient(object):
    
    # Authentication elements
    API_KEY = None
    ACCESS_TOKEN = None
    TIMEOUT = None
    HEADERS = None
    
    # The class "constructor" - It's actually an initializer 
    def __init__(self):
        
        # check if API_KEY is present
        if not os.path.isfile('api_key.txt'):
            raise PlaygroundClientError(500, "A file named 'api_key.txt' with your OneAtlas API key \
                is needed at the root of your directory")
        
        # read API key
        with open('api_key.txt') as f:
            self.API_KEY = f.readline()
            
        # Check status code
        if not self.playground_refresh_access_token():
            raise PlaygroundClientError(500, "A problem occured during connection with the Playground")


    # method to refresh the token 
    def playground_refresh_access_token(self):

        # if ACCESS_TOKEN exists and timeout is not reached, HEADERS should be OK
        if self.ACCESS_TOKEN is not None:
            if self.TIMEOUT is not None:
                if time.time() < self.TIMEOUT:
                    return True

        # request auth token
        r = requests.post('https://authenticate.foundation.api.oneatlas.airbus.com/auth/realms/IDP/protocol/openid-connect/token',
            headers={'Content-Type':'application/x-www-form-urlencoded'},
            data={'apikey':self.API_KEY, 'grant_type':'api_key', 'client_id':'IDP'})

        # Check status code
        if r.status_code != 200:
            raise PlaygroundClientError(r.status_code, 'A problem occured during connection with the Playground')

        # Convert content in json
        content = r.json()

        if not 'access_token' in content.keys():
            raise PlaygroundClientError(500, 'No access_token field in response')
            
        self.ACCESS_TOKEN = content['access_token']

        if not 'expires_in' in content.keys():
            raise PlaygroundClientError(500, 'No expires_in field in response')
            
        expires_in = content['expires_in']
        self.TIMEOUT = time.time() + expires_in // 2

        # build headers
        self.HEADERS = {
            'Authorization': 'Bearer {}'.format(self.ACCESS_TOKEN),
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }
        return True
    
    
    def _get_request(self, template, **kwargs):
        self.playground_refresh_access_token()
        r = requests.get(template.format(**kwargs), headers=self.HEADERS)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            raise PlaygroundClientError(r.status_code, 'This object does not exist')
        elif r.status_code == 401 or r.status_code == 403:
            raise PlaygroundClientError(r.status_code, 'You do not have sufficient rights to perform this operation')
        else:
            raise PlaygroundClientError(r.status_code, 'A problem occured during connection with the Playground')
        return None

    def _post_request(self, template, payload, **kwargs):
        self.playground_refresh_access_token()
        r = requests.post(template.format(**kwargs), data=payload, headers=self.HEADERS)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            raise PlaygroundClientError(r.status_code, 'This object does not exist')
        elif r.status_code == 401 or r.status_code == 403:
            raise PlaygroundClientError(r.status_code, 'You do not have sufficient rights to perform this operation')
        else:
            raise PlaygroundClientError(r.status_code, 'A problem occured during connection with the Playground')
        return None

    def _put_request(self, template, payload, **kwargs):
        self.playground_refresh_access_token()
        r = requests.put(template.format(**kwargs), data=payload, headers=self.HEADERS)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            raise PlaygroundClientError(r.status_code, 'This object does not exist')
        elif r.status_code == 401 or r.status_code == 403:
            raise PlaygroundClientError(r.status_code, 'You do not have sufficient rights to perform this operation')
        else:
            raise PlaygroundClientError(r.status_code, 'A problem occured during connection with the Playground')
        return None

    def _delete_request(self, template, **kwargs):
        self.playground_refresh_access_token()
        r = requests.delete(template.format(**kwargs), headers=self.HEADERS)
        if r.status_code == 200:
            return True
        elif r.status_code == 404:
            raise PlaygroundClientError(r.status_code, 'This object does not exist')
        elif r.status_code == 401 or r.status_code == 403:
            raise PlaygroundClientError(r.status_code, 'You do not have sufficient rights to perform this operation')
        else:
            raise PlaygroundClientError(r.status_code, 'A problem occured during connection with the Playground')
        return False

    #
    # PLAYGROUND API
    #

    # Official Playground URL
    PLAYGROUND_URL = "https://playground.intelligence-airbusds.com"

    # Alternate Playground URL
    #PLAYGROUND_URL = "https://apps.playground.airbusds-geo.com"

    PLAYGROUND_CURRENT_USER_URL = PLAYGROUND_URL + "/currentUser"
    def get_logged_user(self):
        return self._get_request(self.PLAYGROUND_CURRENT_USER_URL)

    PLAYGROUND_PROJECT_URL = PLAYGROUND_URL + "/api/projects"
    def get_projects(self):
        return self._get_request(self.PLAYGROUND_PROJECT_URL)

    PLAYGROUND_PROCESSES_URL = PLAYGROUND_URL + "/api/v1/processes?projectId={projectId}"
    def get_processes(self, projectId):
        return self._get_request(self.PLAYGROUND_PROCESSES_URL, projectId=projectId)

    PLAYGROUND_PROCESS_URL = PLAYGROUND_URL + "/api/v1/processes/{processId}?projectId={projectId}"
    def get_process(self, projectId, processId):
        return self._get_request(self.PLAYGROUND_PROCESS_URL, projectId=projectId, processId=processId)

    PLAYGROUND_DATASETS_URL = PLAYGROUND_URL + "/api/v1/datasets?projectId={projectId}"
    def get_datasets(self, projectId):
        return self._get_request(self.PLAYGROUND_DATASETS_URL, projectId=projectId)

    PLAYGROUND_DATASET_URL = PLAYGROUND_URL + "/api/datasets/{datasetId}"
    def get_dataset(self, datasetId):
        return self._get_request(self.PLAYGROUND_DATASET_URL, datasetId=datasetId)

    PLAYGROUND_ZONES_SEARCH_URL = PLAYGROUND_URL + "/api/zones?dataset_id={datasetId}"
    def get_zones_in_dataset(self, datasetId):
        return self._get_request(self.PLAYGROUND_ZONES_SEARCH_URL, datasetId=datasetId)

    PLAYGROUND_ZONE_ID_URL = PLAYGROUND_URL + "/api/zones/{zoneId}"
    PLAYGROUND_ZONE_URL = PLAYGROUND_URL + "/api/zones"
    def get_zone(self, zoneId):
        return self._get_request(self.PLAYGROUND_ZONE_ID_URL, zoneId=zoneId)
    def store_zone(self, zone, zoneId=None):
        if zoneId == None:
            return self._post_request(self.PLAYGROUND_ZONE_URL, payload=json.dumps(zone))
        else:
            return self._put_request(self.PLAYGROUND_ZONE_ID_URL, payload=json.dumps(zone), zoneId=zoneId)
    def delete_zone(self, zoneId):
        return self._delete_request(self.PLAYGROUND_ZONE_ID_URL, zoneId=zoneId)

    PLAYGROUND_RECORDS_COUNT_ZONE_URL = PLAYGROUND_URL + "/api/records?count=true&zone_id={zoneId}&bbox={BBOX}"
    def get_records_count_in_zone(self, zoneId, bbox):
        return self._get_request(self.PLAYGROUND_RECORDS_COUNT_ZONE_URL, zoneId=zoneId, BBOX=bbox)

    PLAYGROUND_RECORDS_ZONE_URL = PLAYGROUND_URL + "/api/records?zone_id={zoneId}&bbox={BBOX}"
    def get_records_in_zone(self, zoneId, bbox):
        return self._get_request(self.PLAYGROUND_RECORDS_ZONE_URL, zoneId=zoneId, BBOX=bbox)

    PLAYGROUND_RECORD_URL = PLAYGROUND_URL + "/api/records/{recordId}"
    def store_record(self, record, recordId=None):
        if recordId == None:
            return self._post_request(self.PLAYGROUND_RECORD_URL, payload=json.dumps(record))
        else:
            return self._put_request(self.PLAYGROUND_RECORD_URL, payload=json.dumps(record), recordId=recordId)
    def delete_record(self, recordId):
        return self._delete_request(self.PLAYGROUND_RECORD_URL, recordId=recordId)
    
    PLAYGROUND_RECORDS_STORE_URL = PLAYGROUND_URL + "/api/records"
    def store_records(self, payload):
        return self._post_request(self.PLAYGROUND_RECORDS_STORE_URL, payload=payload)
    
    PLAYGROUND_RECORDS_BATCH_DELETE_URL = PLAYGROUND_URL + "/api/recordsbatch/{batchId}/from_dataset/{datasetId}"
    def delete_batch_records(self, datasetId, batchId):
        return self._delete_request(self.PLAYGROUND_RECORDS_BATCH_DELETE_URL, datasetId=datasetId, batchId=batchId)
    
    PLAYGROUND_TAGS_URL = PLAYGROUND_URL + "/api/datasets/{datasetId}/tags"
    def get_tags(self, datasetId):
        return self._get_request(self.PLAYGROUND_TAGS_URL, datasetId=datasetId)
    
    PLAYGROUND_CURRENT_SENSORS_URL = PLAYGROUND_URL + "/api/catalog/constellations"
    def check_available_sensors(self):
        return self._get_request(self.PLAYGROUND_CURRENT_SENSORS_URL)

    PLAYGROUND_SEARCH_URL = PLAYGROUND_URL + "/api/catalog/_search?bbox={bbox}&constellation={sensors}"
    def get_images(self, BBOX, SENSORS):
        return self._get_request(self.PLAYGROUND_SEARCH_URL, bbox=BBOX, sensors=SENSORS)

    PLAYGROUND_SEARCH_UUID_URL = PLAYGROUND_URL + "/api/catalog/uid/{imageUId}"
    def get_image_from_uid(self, imageUId):
        return self._get_request(self.PLAYGROUND_SEARCH_UUID_URL, imageUId=imageUId)

    PLAYGROUND_SEARCH_SOURCEID_URL = PLAYGROUND_URL + "/api/catalog/sourceid/{sourceId}"
    def get_image_from_sourceid(self, sourceId):
        return self._get_request(self.PLAYGROUND_SEARCH_SOURCEID_URL, sourceId=sourceId)

    PLAYGROUND_JOB_URL = PLAYGROUND_URL + "/api/jobs"
    def launch_job(self, data):
        return self._post_request(self.PLAYGROUND_JOB_URL, payload=json.dumps(data))

    PLAYGROUND_JOB_ID_URL = PLAYGROUND_URL + "/api/jobs/{jobId}"
    def get_job(self, jobId):
        return self._get_request(self.PLAYGROUND_JOB_ID_URL, jobId=jobId)


