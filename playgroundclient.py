import json
import requests
import time
import numpy as np
from io import BytesIO
#from multiprocessing import Pool
from queue import Queue
from threading import Thread, Lock
import mercantile
import math
from PIL import Image
import os.path


IMG_MODE = 'RGB'
IMG_SIDE = 256

class NetException(Exception):
    """Tile Exception: generic error for Internet"""
    def __init__(self, message):
        """Tile Exception contructor"""
        super(NetException, self).__init__(message)

class TileException(Exception):
    """Tile Exception: generic error for Tile"""
    def __init__(self, status_code, message):
        """Tile Exception contructor"""
        super(TileException, self).__init__(message)
        self.status_code = status_code

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
    
    # Official Playground URL
    #PLAYGROUND_URL = "https://playground.intelligence-airbusds.com"

    # Alternate Playground URL
    PLAYGROUND_URL = "https://apps.playground.airbusds-geo.com"


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

    PLAYGROUND_ZONE_URL = PLAYGROUND_URL + "/api/zones/{zoneId}"
    def get_zone(self, zoneId):
        return self._get_request(self.PLAYGROUND_ZONE_URL, zoneId=zoneId)
    def store_zone(self, zoneId, zone):
        return self._put_request(self.PLAYGROUND_ZONE_URL, zoneId=zoneId, data=json.dumps(zone))

    RECORDS_COUNT_ZONE_URL = PLAYGROUND_URL + "/api/records?count=true&zone_id={zoneId}&bbox={BBOX}"
    def get_records_count_in_zone(self, zoneId, bbox):
        return self._get_request(self.RECORDS_COUNT_ZONE_URL, zoneId=zoneId, BBOX=bbox)

    RECORDS_ZONE_URL = PLAYGROUND_URL + "/api/records?zone_id={zoneId}&bbox={BBOX}"
    def get_records_in_zone(self, zoneId, bbox):
        return self._get_request(self.RECORDS_ZONE_URL, zoneId=zoneId, BBOX=bbox)

    RECORDS_URL = PLAYGROUND_URL + "/api/records/{recordId}"
    def delete_record(self, recordId):
        return self._delete_request(self.RECORDS_URL, recordId=recordId)

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

    # function to get a single XYZ tile
    def get_tile(self, xyz_url, z, x, y):
        self.playground_refresh_access_token()
        r = requests.get(xyz_url.format(z=z, x=x, y=y), headers=self.HEADERS)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content))
        elif r.status_code == 404 or r.status_code == 204:
            return Image.new(IMG_MODE, (IMG_SIDE, IMG_SIDE), "black")
        elif r.status_code == 401 or r.status_code == 403:
            raise PlaygroundClientError(r.status_code, 'You do not have sufficient rights to perform this operation')
        else:
            raise PlaygroundClientError(r.status_code, 'A problem occured during connection with the Playground')
        return None    
    
    # multithreaded functions to get multiple XYZ tiles and combine them into a large tile
    def get_big_tile(self, nbtiles, xyz_url, zoom, col, row):
        big_tile = Image.new(IMG_MODE, (IMG_SIDE * nbtiles, IMG_SIDE * nbtiles))
        offset = nbtiles // 2

        # Get Lock
        queueLock = Lock()

        def patchwork(q):
            while True:
                args = q.get()
                if args is None:
                    #print("Received None -> exiting")
                    break
                (j, i) = args
                #print("Processing {}/{}".format(j, i))
                c = col - offset + i
                r = row - offset + j
                try:
                    img = self.get_tile(xyz_url, zoom, c, r)
                except (TileException, NetException) as te:
                    print("In except clause: putting {}/{} back in queue".format(j, i))
                    q.put(args)
                    continue
                finally:
                    q.task_done()

                # paste in big image making sure that it is thread-safe
                queueLock.acquire()
                big_tile.paste(img, (i * IMG_SIDE, j * IMG_SIDE))
                queueLock.release()

        matrix = [[(j, i) for j in range(nbtiles)] for i in range(nbtiles)]
        patches = [item for sublist in matrix for item in sublist]
        #print(patches)

        q = Queue(100000)
        for p in patches:
            q.put(p)

        threads = []
        num_worker_threads = 8
        for _ in range(num_worker_threads):
            t = Thread(target=patchwork, args=(q,))
            t.start()
            threads.append(t)

        # block until all tasks are done
        q.join()

        # stop workers
        for i in range(num_worker_threads):
            q.put(None)
        for t in threads:
            t.join()

        return big_tile
    
    # creates the corresponding PROJ file to the previous image
    def get_big_tile_proj(self, nbtiles, zoom, col, row):

        col_min = col - nbtiles // 2
        row_min = row - nbtiles // 2

        (easting, northing) = num2merc(col_min, row_min, zoom)
        content = str(2.0 * maxvalue / (2.0 ** zoom) / 256.0) + "\n"
        content += "0.0\n"
        content += "0.0\n"
        content += str(-2.0 * maxvalue / (2.0 ** zoom) / 256.0) + "\n"
        content += str(easting) + "\n"
        content += str(northing) + "\n"
        return content


    
# some useful function to convert to WebMercator
# maxvalue = 2 * math.pi * 6378137 / 2.0
maxvalue = 20037508.342789244

def merc2num(easting, northing, zoom):
    n = 2.0 ** zoom
    xtile = int((easting / maxvalue + 1.0) / 2.0 * n)
    ytile = int((1.0 - northing / maxvalue) / 2.0 * n)
    return (xtile, ytile)

def num2merc(xtile, ytile, zoom):
    n = 2.0 ** zoom
    easting = (2.0 * xtile / n - 1.0) * maxvalue
    northing = (1.0 - 2.0 * ytile / n) * maxvalue
    return (easting, northing)