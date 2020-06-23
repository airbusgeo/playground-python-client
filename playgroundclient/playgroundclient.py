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

# http://www.neercartography.com/latitudelongitude-tofrom-web-mercator/
# http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/

# WGS84 spheriod semimajor axis
SEMI_MAJOR_AXIS = 6378137.0

# maxvalue = 2 * math.pi * 6378137.0 / 2.0
MAX_VALUE = 20037508.342789244


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
    PLAYGROUND_URL = "https://playground.intelligence-airbusds.com"

    # Alternate Playground URL
    #PLAYGROUND_URL = "https://apps.playground.airbusds-geo.com"


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
    
    PLAYGROUND_TAGS_URL = "https://playground.intelligence-airbusds.com/api/datasets/{datasetId}/tags"
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
    PLAYGROUND_JOB_ID_URL = PLAYGROUND_URL + "/api/jobs/{jobId}"
    def get_job(self, jobId):
        return self._get_request(self.PLAYGROUND_JOB_ID_URL, jobId=jobId)
    def launch_job(self, data):
        return self._post_request(self.PLAYGROUND_JOB_URL, payload=json.dumps(data))

    # function to get a single XYZ tile
    def get_tile(self, xyz_url, z, x, y):
        self.playground_refresh_access_token()
        try:
            r = requests.get(xyz_url.format(z=z, x=x, y=y), headers=self.HEADERS)
        except Exception as e:
            raise NetException('A problem occured while while connecting to the Tile service: ' + str(e))

        if r.status_code == 200:
            return Image.open(BytesIO(r.content))
        elif r.status_code == 404 or r.status_code == 204:
            return Image.new(IMG_MODE, (IMG_SIDE, IMG_SIDE), "black")
        elif r.status_code == 401 or r.status_code == 403:
            raise PlaygroundClientError(r.status_code, 'You do not have sufficient rights to perform this operation')
        else:
            raise TileException(r.status_code, 'A problem occured while retrieving tile from Playground')
        return None    
    
    @staticmethod
    def emptyQueue(q):
        while True:
            q.task_done()
            args = q.get()
            if args is None:
                break

    # multithreaded functions to get multiple XYZ tiles and combine them into a large tile
    def get_big_tile(self, nbtiles, xyz_url, zoom, col, row, num_worker_threads = 8):
        big_tile = Image.new(IMG_MODE, (IMG_SIDE * nbtiles, IMG_SIDE * nbtiles))
        offset = nbtiles // 2

        # Get Lock
        queueLock = Lock()

        def patchwork(q):
            counter = 0
            max_retries = 20
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
                except (NetException, TileException) as e:
                    print("Catched an error: " + str(e))
                    if counter < max_retries:
                        print("==> Putting {}/{} back in queue.".format(j, i))
                        q.put(args)
                        counter += 1
                        continue
                    else:
                        # there is an error and we've tried enough times
                        emptyQueue(q)
                        raise e
                except (PlaygroundClientError) as e:
                        emptyQueue(q)
                        raise e
                finally:
                    q.task_done()

                counter = 0
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
        for _ in range(num_worker_threads):
            t = Thread(target=patchwork, args=(q,))
            t.start()
            threads.append(t)

        # block until all tasks are done
        q.join()

        # stop workers
        for _ in range(num_worker_threads):
            q.put(None)
        for t in threads:
            t.join()

        return big_tile
    
    """
    USEFUL GEOGRAPHICAL COMPUTATIONS
    """

    @staticmethod
    def merc2num(easting, northing, zoom):
        n = 2.0 ** zoom
        xtile = int((easting / MAX_VALUE + 1.0) / 2.0 * n)
        ytile = int((1.0 - northing / MAX_VALUE) / 2.0 * n)
        return (xtile, ytile)

    @staticmethod
    def num2merc(xtile, ytile, zoom):
        n = 2.0 ** zoom
        easting = (2.0 * xtile / n - 1.0) * MAX_VALUE
        northing = (1.0 - 2.0 * ytile / n) * MAX_VALUE
        return (easting, northing)

    @staticmethod
    def merc2geog(easting, northing):

        # Check if coordinate out of range for Web Mercator
        # 20037508.342789244 is full extent of Web Mercator
        if (abs(easting) > MAX_VALUE) or (abs(northing) > MAX_VALUE):
            #raise ValueError
            return float('NaN'), float('NaN')

        latitude = (1.5707963267948966 - (2.0 * math.atan(math.exp((-1.0 * northing) / SEMI_MAJOR_AXIS)))) * (180.0 / math.pi)
        longitude = ((easting / SEMI_MAJOR_AXIS) * 57.295779513082323) - ((math.floor((((easting / SEMI_MAJOR_AXIS) * 57.295779513082323) + 180.0) / 360.0)) * 360.0)

        return longitude, latitude

    @staticmethod
    def geog2merc(lon, lat):
        # Check if coordinate out of range for Latitude/Longitude
        if (abs(lon) > 180.0) and (abs(lat) > 90.0):
            return float('NaN'), float('NaN')

        east = lon * 0.017453292519943295
        north = lat * 0.017453292519943295

        northing = 3189068.5 * math.log((1.0 + math.sin(north)) / (1.0 - math.sin(north)))
        easting = SEMI_MAJOR_AXIS * east

        return easting, northing

    # creates the corresponding PROJ file to the previous image
    @staticmethod
    def get_big_tile_proj(nbtiles, zoom, col, row):

        col_min = col - nbtiles // 2
        row_min = row - nbtiles // 2

        (easting, northing) = PlaygroundClient.num2merc(col_min, row_min, zoom)
        content = str(2.0 * MAX_VALUE / (2.0 ** zoom) / 256.0) + "\n"
        content += "0.0\n"
        content += "0.0\n"
        content += str(-2.0 * MAX_VALUE / (2.0 ** zoom) / 256.0) + "\n"
        content += str(easting) + "\n"
        content += str(northing) + "\n"
        return content

    # function to convert pixels in a WebMercator JPEG image into lon/lat (using params from JGW)
    @staticmethod
    def pixel2geographic(px, py, param):

        # get easting,northing in WebMercator
        easting = param[0] * px + param[2] * py + param[4]
        northing = param[1] * px + param[3] * py + param[5]

        # convert to lat,long
        return PlaygroundClient.merc2geog(easting, northing)


    # function to convert lon/lat to pixels in a WebMercator JPEG image (using params from JGW)
    @staticmethod
    def geographic2pixel(lng, lat, param):

        # convert to lat,long
        easting, northing = PlaygroundClient.geog2merc(lng, lat)
        #print(easting, northing)

        # to pixels
        x = (param[2] * (northing - param[5]) - param[3] * (easting - param[4])) / (param[1] * param[2] - param[0] * param[3])
        y = (param[1] * (easting - param[4]) - param[0] * (northing - param[5])) / (param[1] * param[2] - param[0] * param[3])

        return round(x), round(y)

