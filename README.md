## godata-extract-qgis-plugin
This Plugin for QGIS enables users to log in to [Go.Data](https://worldhealthorganization.github.io/godata/) and extract case data from within QGIS. Go.Data is an application which facilitates outbreak investigation, including field data collection, contact tracing, and visualization of chains of transmission. This plugin will extract data from the Go.Data API and will transform the JSON output to multiple csv files. The Plugin was created for somebody in the GIS role during emergency responses. Specifically, they can access outbreak data, extract case data, and automate the process to create maps for outbreak investigation and incident management. 

For ESRI ArcGIS Pro users, please find our similar offering [here](https://github.com/WorldHealthOrganization/godata-ESRI-SITREP-toolbox).

## Requirements
- Go.Data URL, username and password
- Name of the outbreak you wish to extract data for
- GIS layer for mapping (optional)
- [QGIS](https://qgis.org/en/site/forusers/download.html) (plugin is known to be compatible with 3.22.11, 3.28.1, 3.4.7 and 3.22.14 - current LTR)
- This plugin is currently functioning with Go.Data version 44

## Set up 
There is no need to download the plugin from this repo, it can be added from the plugin manager within QGIS. Instructions for installing [Plugins](https://docs.qgis.org/3.22/en/docs/training_manual/qgis_plugins/fetching_plugins.html). Should you be operating offline and need to install locally - download zip from this repo and import the zip file via the QGIS plugin manager.

## Dependencies
Please note that this plugin utilizes the 'Pandas' python library. The OSGeo4W/QGIS installation includes its own Python 3 environment and you will have make sure that pandas is included in this Python installation. To update your QGIS Python environment with the Pandas library, please watch the following quick [tutorial](https://youtu.be/vJXrD4_aF-o) to walk through the steps for installation.

## Help
In case you're experiencing any challenge while using this plugin, or if you have enhancements to suggest, please comment [here](https://github.com/WorldHealthOrganization/godata-extract-qgis-plugin/issues).

## About
This plugin is a part of a series of open source projects developed as part of an informal collaboration between the WHO GIS Centre for Health and the GIS focal point of the GOARN Go.Data team. The aim of the collaboration is to provide free open source tools to improve a GIS user's ability to access, transfom, analyze and visualize public health data geospatially, especially during an emergency response.

Projects:
- [ESRI SITREP toolbox](https://github.com/WorldHealthOrganization/godata-ESRI-SITREP-toolbox) - released February, 2022
- [QGIS Extract plugin](https://github.com/WorldHealthOrganization/godata-extract-qgis-plugin) - released December, 2022

Project team:

Developer: Adam McKay, adam@addressdatamatters.ca  
Project Manager: Amy Louise Lang, Langstervision@gmail.com
