FROM ubuntu:18.04

# This is necessary for apt to access HTTPS sources
RUN apt-get update && \
    apt-get install apt-transport-https

# Conf
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=C.UTF-8

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Pick up some dependencies
RUN apt-get update --fix-missing && \
        apt-get install -y --no-install-recommends \
                bash \
                vim \
                build-essential \
                python3-pip \
                python3-dev \
                python3-opencv \
                python3-shapely \
                bzip2 \
                libsm6 \
                libxext6 \
                cmake \
                ca-certificates \
                curl \
                git \
                libgl1-mesa-glx \
                software-properties-common \
                gnupg2 \
                tmux \
                graphviz \
                unzip \
                wget \
                ssh \
        && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*

# Replace python2 by python3
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Get GDAL (stable on 18.04)
RUN add-apt-repository -y ppa:ubuntugis/ppa && \
        apt-get update -y && \
        apt-get upgrade -y && \
        apt-get install -y \
                gdal-bin \
                python-numpy \
                python-gdal \
                libgdal-dev \
        && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*

# Get NodeJS
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs
RUN nodejs -v

RUN ln -sf /usr/bin/python3 /usr/bin/python & \
    ln -sf /usr/bin/pip3 /usr/bin/pip

RUN pip install --upgrade pip

# Main Pytonh libraries
RUN pip install setuptools-scm &&  \
        pip install --upgrade setuptools && \
        pip install --upgrade numpy==1.17 && \
        pip install --upgrade pandas && \
        pip install --upgrade opencv-python && \
        pip install --upgrade rasterio && \
        pip install --upgrade Pillow==6.2.1 && \
        pip install --upgrade tornado && \
        pip install --upgrade requests && \
        pip install --upgrade requests_toolbelt && \
        pip install --upgrade ipywidgets && \
        pip install --upgrade ipyleaflet && \
        pip install --upgrade jupyterthemes && \
        pip install --upgrade jupyterlab
        
RUN jupyter labextension install jupyter-leaflet
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

# Specific requirements for current project
COPY requirements.txt .
RUN pip install --upgrade -r requirements.txt

# Get current user from BUILD parameters
ARG USER_ID
ARG GROUP_ID

# Create a local jovyan user in container with same UID and GID
RUN addgroup --gid $GROUP_ID jovyan; exit 0
RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID jovyan

# Switch back to jovyan to avoid accidental container runs as root
USER jovyan

# Generate configuration and set password as 'password' (change with passwd() from notebook.auth)
RUN jupyter notebook --generate-config
RUN echo "c.ServerApp.password='sha1:da0014b37d99:8b1fe5702d694e65462951262685da2c199facd2'">>$HOME/.jupyter/jupyter_notebook_config.py

# Jupyter entrypoint in /home/jovyan/code
WORKDIR /home/jovyan/code/

# Adding local pip install to PATH
ENV PATH="/home/jovyan/.local/bin:${PATH}"

# IPython
EXPOSE 8080

ENTRYPOINT ["jupyter", "lab", "--port=8080", "--ip=0.0.0.0", "--ServerApp.iopub_data_rate_limit=1.0e10"]
