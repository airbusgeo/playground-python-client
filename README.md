# Jupyter Notebooks examples of Playground API scripts

## Connecting to the API

To connect to the API, you need to retrieve your API_KEYS from the OneAtlas website. Follow the simple steps below:

1. Visit this URL: https://data.api.oneatlas.airbus.com/api-keys
2. Click the **Create and API key** button
3. Enter a description for your API_KEY (e.g. Playground Keys)
4. Store the file in the same folder than this notebook and name it **api_key.txt**

Make sure to keep your **api_key.txt** safe! Do not include it in a public github repository for example :-)

The following script will then use this **api_key.txt** file to generate an ACCESS_TOKEN. We will store this ACCESS_TOKEN in HEADERS that we will send with each requests. The ACCESS_TOKEN has a timeout so we will create a function that renew the ACCESS_TOKEN when half of the timeout has expired. 
