# Intelligence Playground Python Client

This repository contains a Python Library to easy connection to the Airbus Intelligence Playground API.
It also provide some example of requests organized by themes in Python Notebooks.

## Install the Playground API Library

First clone this repository:
```git clone https://github.com/airbusgeo/playground-python-client.git```

Then open a command shell, go to the repository folder and type the following command:
```pip install .```
or if your have already installed the client and want to upgrade:
```pip install --upgrade .```

This will install the Playground API Client in your local Python libraries.

### Get and store your API key

To connect to the API, you need to retrieve your API_KEYS from the OneAtlas website. Follow the simple steps below:

1. Visit this URL: https://data.api.oneatlas.airbus.com/api-keys
2. Click the **Create and API key** button
3. Enter a description for your API_KEY (e.g. Playground Keys)
4. Store the file in the same folder than this notebook and name it **api_key.txt**

Make sure to keep your **api_key.txt** safe! Do not include it in a public github repository for example :-)

The following script will then use this **api_key.txt** file to generate an ACCESS_TOKEN. We will store this ACCESS_TOKEN in HEADERS that we will send with each requests. The ACCESS_TOKEN has a timeout so we will create a function that renew the ACCESS_TOKEN when half of the timeout has expired. 

### Run the examples in Jupyter Notebook from Docker container (optional)

You can run the **Jupyter Notebook** examples to get familiar with the Playground Client. If you do not have a running Jupyter environment, you can run **Jupyter Lab** with the help of the **Docker** file that we provide. Just run the following command `./run_docker.sh --build` to create and run the container. After the Docker image has been built, you just need to run `./run_docker.sh`.

When the container is running, just open your browser and navigate to http://localhost:8080. The password is `password`.


## How to create the Playground Client in your Python scripts

Just import and create an instance of the PlaygroundClient object:

```python
# Connect to the Playground API 
from playgroundclient import PlaygroundClient
play = PlaygroundClient()
```

You can start using the client immediately:

```python
# Logged in user
user = play.get_logged_user()
print("Logged as user: {} {}".format(user['firstname'], user['lastname']))
```

## Jupyter Notebooks examples of Playground API scripts

This notebooks presents some useful task with Playground:
* Getting started
* Working with imagery (searching and displaying)

