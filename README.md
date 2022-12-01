# godata-extract-qgis-plugin
This is a Plugin for QGIS that enables users to log in to Go.Data and extract case data. Go.Data is an application which facilitates outbreak investigation, including field data collection, contact tracing, and visualization of chains of transmission. Go.Data utilizes Mongo.db, so this plugin will extract data from it utilizing APIs and it will transform the JSON output to multiple csv files. This Plugin was created to allow someone in the GIS role of outbreak emergency response to access the outbreak data, extract case and contact data, and automate the process to create maps for outbreak investigation.

Instructions for installing [Plugins](https://docs.qgis.org/3.22/en/docs/training_manual/qgis_plugins/fetching_plugins.html)

Please note that this plug utilizes the Pandas python library. Should you need to install it, here is a [tutorial](https://youtu.be/vJXrD4_aF-o) to walk through the steps for installation.


