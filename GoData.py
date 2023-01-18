# -*- coding: utf-8 -*-
"""
/***************************************************************************
 goDataExtract
                                 A QGIS plugin
 This plugin extracts data from the Go.Data API
                              -------------------
        begin                : 2022-05-09
        email                : adam@addressdatamatters.ca; Langstervision@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QProgressBar
from qgis.core import Qgis, QgsMessageLog, QgsVectorLayer, QgsProject
import processing

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .GoData_dialog import goDataExtractDialog
import ast
from urllib import request
import json
import requests
import pandas as pd
import collections
from datetime import datetime, timedelta
from pathlib import Path

class goDataExtract:

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        # self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        # locale = QSettings().value('locale/userLocale')[0:2]
        # locale_path = os.path.join(
        #     self.plugin_dir,
        #     'i18n',
        #     'goDataExtract_{}.qm'.format(locale))

        # if os.path.exists(locale_path):
        #     self.translator = QTranslator()
        #     self.translator.load(locale_path)
        #     QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Go Data Extraction')
        
        self.selected_outbreak_id = None
        self.selected_outbreak_name= None
        self.outbreaks_cache = {}
        self.available_outbreaks = []
        self.in_gd_api_url = None
        self.in_gd_username = None
        self.in_gd_password = None
        self.in_gd_output_path = None
        self.in_gd_locate_folder_btn = None
        self.access_token = None
        self.locations_df = None
        self.locations_reorg_df = None
        self.cases_df = None
        self.admin_level = ''
        self.tabular_join_field = None
        self.in_gd_locate_shp_btn = None
        self.in_gd_shape = None
        self.shp_stem = None
        self.in_gd_field = None
        self.in_gd_geojoin_box = None
        self.vector_layer = None
        

        self.right_now = datetime.now()
        self.timestamp = self.right_now.strftime('%Y-%m-%d_%H%M%S')
        self.yesterday_delta = timedelta(days=1)
        self.eight_days_delta = timedelta(days=8)
        self.fifteen_days_delta = timedelta(days=15)
        self.twenty_eight_days_delta = timedelta(days=28)
        self.one_week_delta = timedelta(weeks=1)
        self.two_week_delta = timedelta(weeks=2)

        self.yesterday = (self.right_now - self.yesterday_delta).date()
        self.seven_days_ago = (self.right_now - self.one_week_delta).date()
        self.eight_days_ago = (self.right_now - self.eight_days_delta).date()
        self.fourteen_days_ago = (self.right_now - self.two_week_delta).date()
        self.fifteen_days_ago = (self.right_now - self.fifteen_days_delta).date()
        self.twenty_eight_days_ago = (self.right_now - self.twenty_eight_days_delta).date()

        self.out_summary_data = 'Cases by reporting area'

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('goDataExtract', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GoData/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Go Data Extract'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Go Data Extraction'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = goDataExtractDialog()
            self.dlg.in_gd_locate_folder_btn.clicked.connect(self.in_gd_locate_folder)
            self.dlg.in_gd_locate_shp_btn.clicked.connect(self.in_gd_locate_shp_path)
            self.dlg.in_gd_get_outbreaks.clicked.connect(self.get_token)
            self.dlg.in_gd_geojoin_box.clicked.connect(self.include_geo)
            self.dlg.gd_ok.clicked.connect(self.get_cases)   
            self.dlg.gd_cancel.clicked.connect(self.reject)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def reject(self):
        self.dlg.in_gd_password.clear()
        self.dlg.in_gd_ob_dd.clear()
        self.dlg.in_gd_output_path.clear()
        # self.dlg.in_gd_shape.clear()
        self.dlg.in_gd_geojoin_box.setChecked(False)
        self.include_geo()
        # self.dlg.in_gd_fld_dd.clear()
        self.dlg.reject()
    
    def include_geo(self):
        if self.dlg.in_gd_geojoin_box.isChecked():
            self.dlg.in_gd_shape.setEnabled(True)
            self.dlg.in_gd_locate_shp_btn.setEnabled(True)
        elif not self.dlg.in_gd_geojoin_box.isChecked():
            self.dlg.in_gd_shape.setEnabled(False)
            self.dlg.in_gd_locate_shp_btn.setEnabled(False)
            self.dlg.in_gd_fld_dd.setEnabled(False)
            self.dlg.in_gd_fld_dd.clear()
            self.dlg.in_gd_shape.clear()


    def join_to_geo(self):
        uri = f'file:///{self.in_gd_output_path}/{self.out_summary_data}.csv?delimiter=,&decimal=.'    
        summary_data = QgsVectorLayer(uri, 'in_memory_layer', 'delimitedtext')      
        self.in_gd_field = self.dlg.in_gd_fld_dd.currentText().rsplit(' - ', 2)[0]
      
        params = {'INPUT': self.vector_layer, 
                    'FIELD':self.in_gd_field, 
                    'INPUT_2':summary_data, 
                    'FIELD_2':self.tabular_join_field, 
                    'OUTPUT': 'memory:'}

        result = processing.run('native:joinattributestable', params)
        result_layer = result['OUTPUT']
        result_layer.setName(f'{self.shp_stem}_Outbreaks_{self.timestamp}')
        QgsProject.instance().addMapLayer(result_layer)

    def in_gd_locate_shp_path(self):
        shp_path_dir = QFileDialog.getOpenFileName(parent=None, caption= u'Select Shapefile', filter='Shapefile (*.shp)') #  returns a list within a tuple
        self.dlg.in_gd_shape.setText(shp_path_dir[0]) 
        self.in_gd_shape = self.dlg.in_gd_shape.text()
        self.shp_stem = Path(self.dlg.in_gd_shape.text()).stem
        self.vector_layer = QgsVectorLayer(self.in_gd_shape, self.shp_stem)
        vector_fields = self.vector_layer.fields()
        self.dlg.in_gd_fld_dd.clear()
        self.dlg.in_gd_fld_dd.setEnabled(True)
        for fld in vector_fields:
            self.dlg.in_gd_fld_dd.addItem(fld.name() + ' - ' + fld.typeName())

    def set_in_gd_output_path(self):
        if not self.in_gd_output_path and not self.dlg.in_gd_output_path.text():
            QMessageBox.critical(self.dlg, 'Error', 'Please enter a valid output path')
            return None
        else:
            self.in_gd_output_path = self.dlg.in_gd_output_path.text()
            return self.in_gd_output_path

    def in_gd_locate_folder(self):
        output_path_dir = QFileDialog.getExistingDirectory(parent=None, caption= u'Select Folder')
        self.dlg.in_gd_output_path.setText(output_path_dir)
        self.in_gd_output_path = self.dlg.in_gd_output_path.text()

    def get_token(self):
        self.in_gd_api_url = self.dlg.in_gd_api_url.text()
        self.in_gd_username = self.dlg.in_gd_username.text()
        self.in_gd_password = self.dlg.in_gd_password.text()

        if not self.in_gd_api_url or not self.in_gd_username or not self.in_gd_password:
            QMessageBox.about(self.dlg, 'Warning', 'Please fill in all parameters')
            return

        req = request.Request(f'{self.in_gd_api_url}/api/oauth/token', method='POST')
        req.add_header('Content-Type', 'application/json')
        data = {
            'username': self.in_gd_username,
            'password': self.in_gd_password 
            }
        data = json.dumps(data)
        data = data.encode()
        
        try:
            r = request.urlopen(req, data=data).read().decode('utf-8')
        except Exception as e:
            if '401' in str(e):
                QMessageBox.critical(self.dlg, 'Error', 'Connection to Go.Data Failed with HTTP Response:\n'+ str(e) + '\n\nPlease check username, password')
                self.dlg.in_gd_password.clear()
                return
            elif '404' in str(e):
                QMessageBox.critical(self.dlg, 'Error', 'Connection to Go.Data Failed with HTTP Response:\n'+ str(e) + '\n\nPlease check url')
                self.dlg.in_gd_api_url.clear()
            else:
 
                QMessageBox.critical(self.dlg, 'Error', 'Connection to Go.Data Failed with HTTP Response:\n'+ str(e))

        self.access_token = ast.literal_eval(r)['access_token']
        QgsMessageLog.logMessage(f'Go.Data Token acquired: {self.access_token}', level=Qgis.Info)
        self.get_outbreaks()
        return      
      
    def get_outbreaks(self):
        self.dlg.in_gd_ob_dd.clear()
        QgsMessageLog.logMessage(f'Getting outbreaks available for user: {self.in_gd_username}', level=Qgis.Info)
        params = { 'access_token': self.access_token }
        outbreaks_res = requests.get(f'{self.in_gd_api_url}/api/outbreaks', params=params)
        outbreaks_res_json = outbreaks_res.json()
        if 'error' in outbreaks_res_json:
            message = outbreaks_res_json['error']['message']
            QMessageBox.critical(self.dlg, 'Error', message)
            return 
        
        self.available_outbreaks[:] = []
        for outbreak in outbreaks_res_json:
            name = outbreak['name']
            id = outbreak['id']
            self.available_outbreaks.append(name)
            self.outbreaks_cache[name]=id

        for outbreak in self.available_outbreaks:
            # if outbreak not in [self.dlg.in_gd_ob_dd.itemText(i) for i in range(self.dlg.in_gd_ob_dd.count())]:
            self.dlg.in_gd_ob_dd.addItem(outbreak)

        QgsMessageLog.logMessage(f'Connected to GoData API!', level=Qgis.Success)
    

    def get_locations(self):  
        params = {            "access_token": self.access_token,
        }
        location_data = requests.get(f'{self.in_gd_api_url}/api/locations', params=params)
        location_data_json = location_data.json()
        QgsMessageLog.logMessage(f'Found locations! There are {len(location_data_json)} locations found for the {self.selected_outbreak_name} outbreak', level=Qgis.Success)
       
        features = []
        for loc in location_data_json:
            feature = {}
            keys = loc.keys()
            for key in keys:
                if key == 'geoLocation':
                    if loc[key] == None:
                        pass
                    else:
                        feature['Lat'] = loc[key]['lat']
                        feature['Lng'] = loc[key]['lng'] 
                if key == 'geographicalLevelId':
                    feature['adminLevel'] = int(loc[key].split('_')[-1])
                elif not isinstance(loc[key], collections.abc.Mapping) and not isinstance(loc[key], list):
                    loc_value = loc[key]
                    feature[key] = loc_value        
            features.append(feature)

        if not self.set_in_gd_output_path():
            return

        self.locations_df = pd.DataFrame(features)
        self.locations_df.to_csv(f'{self.in_gd_output_path}/locations.csv', index=False, encoding='utf-8-sig')  
        self.reorganized_locations = pd.DataFrame()
        self.locations_reorg_df = self.reorganize_locations(self.locations_df)

    def progressions(self, msg, val):
        self.iface.messageBar().clearWidgets()
        self.progressMessageBar = self.iface.messageBar().createMessage(msg)
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.progressMessageBar.layout().addWidget(self.progress)
        self.iface.messageBar().pushWidget(self.progressMessageBar, Qgis.Info)
        self.progress.setValue(val)
        QgsMessageLog.logMessage(msg, level = Qgis.Success)

    def get_cases(self):
        self.progressions('Starting plugin', 0)
        if not self.access_token:
            QMessageBox.about(self.dlg, 'Warning', 'Please aquire an access token by providing valid username and password \n and then clicking \'Connect\'')
            return

        if self.dlg.in_gd_geojoin_box.isChecked() and not self.in_gd_shape:
            QMessageBox.about(self.dlg, 'Warning', 'Please provide a pathway to a shapefile \n or unselect \'Join to shapefile\'')
            return

        self.progressions('Getting Cases', 1)
        
        self.selected_outbreak_name = self.dlg.in_gd_ob_dd.currentText()
        self.selected_outbreak_id = self.outbreaks_cache[self.selected_outbreak_name]
        params = { 
            'access_token': self.access_token 
            }
        case_data = requests.get(f'{self.in_gd_api_url}/api/outbreaks/{self.selected_outbreak_id}/cases', params=params)
        case_data_json = case_data.json()

        QgsMessageLog.logMessage(f'Found cases!  There are {len(case_data_json)} cases in the {self.selected_outbreak_name} outbreak', level=Qgis.Success)

        self.progressions('Getting Locations', 20)

        self.get_locations()

        self.progressions('Cleaning Cases', 30)

        features = []
        for case in case_data_json:
            feature = {}
            keys = case.keys()
            for key in keys:
                if key == 'age':
                    if 'years' in case[key]:
                        feature['age_years'] = case[key]['years']
                    if 'months' in case[key]:
                        feature['age_months'] = case[key]['months']
                        feature['age_years']= 0
                
                elif key == 'addresses':
                    address = case[key][0]
                    location_id = address['locationId']
                    feature['locationId'] = location_id ## do not remove
                    feature['locationClassification'] = address['typeId']
                    if 'city' in address:
                        feature['city'] = address['city']
                    if 'postalCode' in address:
                        feature['postalCode'] = address['postalCode']
                    if 'addressLine1' in address:
                        feature['addressLine1'] = address['addressLine1']  
                elif key == 'locations':
                    if len(case[key]) > 0:
                        location = case[key][0]
                        feature['adminLevel'] = location['geographicalLevelId'].split('_')[-1]
                elif key == 'dob':
                    feature['dateOfBurial'] = case[key]
                elif key == 'vaccinesReceived':
                    if len(case[key]) > 0:
                        feature['vaccinated'] = 'True'
                    else:
                        feature['vaccinated'] = 'False'
                elif not isinstance(case[key], collections.abc.Mapping) and not isinstance(case[key], list):
                    case_value = case[key]     
                    feature[key] = case_value 
            features.append(feature)  
    
        if not self.set_in_gd_output_path():
            return

        self.cases_df = pd.DataFrame(features)
        self.get_admin_level()
        self.progressions('Joining location data to case data', 45)
        self.join_locs_to_cases()
        self.progressions('Cleaning reference data', 60)
        self.clean_ref_data(self.cases_df)
        self.progressions('Enhancing case data', 75)
        self.update_date_fields(self.cases_df)
        self.get_age_groups(self.cases_df)

        self.cases_df.loc[self.cases_df[f'admin_{self.admin_level}_name'].isna(), f'admin_{self.admin_level}_name'] = 'No Location Provided'
        self.cases_df.loc[self.cases_df[f'admin_{self.admin_level}_LocationId'].isna(), f'admin_{self.admin_level}_LocationId'] = 'No Location Provided'
        self.cases_df.to_csv(f'{self.in_gd_output_path}/cases.csv', index = False, encoding='utf-8-sig')
        self.progressions('Summarizing cases by location', 80)
        self.summarize_cases(self.cases_df)
        if self.dlg.in_gd_geojoin_box.isChecked():
            self.progressions('Joining summarized cases to shapefile', 90)
            self.join_to_geo()
        self.progressions('Complete', 100)

        # self.iface.messageBar().clearWidgets()
        self.dlg.accept()

    def get_admin_level(self):
        all_loc_ids =  self.locations_df[['id', 'adminLevel']].loc[self.locations_df['adminLevel']!=-1].rename(columns={'id':'locationId'}).set_index('locationId')
        all_cases_loc_ids = self.cases_df.groupby('locationId', as_index=False).count()[['locationId', 'id']].rename(columns={'id':'cnt'}).set_index('locationId')
        self.admin_level = int(all_cases_loc_ids.join(all_loc_ids, how='left').groupby('adminLevel')['cnt'].sum().idxmax())
        self.tabular_join_field =f'admin_{self.admin_level}_LocationId'
        QgsMessageLog.logMessage(f'Most commonly used Admin Level: {str(self.admin_level)}', level=Qgis.Info)
    
    def join_locs_to_cases(self):
        location_flds = [f'admin_{i}_name' for i in range(int(self.admin_level)+1)]
        location_flds.extend([self.tabular_join_field, f'admin_{self.admin_level}_Lat', f'admin_{self.admin_level}_Lng'])
        locations_join = self.locations_reorg_df[location_flds].copy()
        locations_join.rename(columns = {f'admin_{self.admin_level}_Lat':'Lat',
                                        f'admin_{self.admin_level}_Lng':'Lng'}, inplace=True)
        self.cases_df = pd.merge(self.cases_df, locations_join, how='left', left_on='locationId', right_on=self.tabular_join_field)

    def reorganize_locations(self, loc_df):
        try:
            for i in range(6):
                flds = ['name', 'parentLocationId', 'id', 'Lat', 'Lng']
                currentlocid = f'admin_{i}_LocationId'
                parentlocid = f'admin_{i-1}_LocationId'
                currentname = f'admin_{i}_name'
                lat = f'admin_{i}_Lat'
                lng = f'admin_{i}_Lng'
                aux_df  = pd.DataFrame()
                if i == 0:
                    self.reorganized_locations = loc_df.loc[loc_df['adminLevel']==i].copy()
                    self.reorganized_locations = self.reorganized_locations[flds]
                    self.reorganized_locations.rename(columns = {'id': currentlocid,
                                            'name': currentname,
                                            'Lat':lat,
                                            'Lng':lng}, inplace=True)

                else:
                    aux_df = loc_df.loc[loc_df['adminLevel']== i].copy()
                    aux_df = aux_df[flds]
                    aux_df.rename(columns = {'id': currentlocid,
                                                'parentLocationId': parentlocid,
                                                'name': currentname,
                                                'Lat':lat,
                                                'Lng':lng}, inplace=True)
                    self.reorganized_locations = self.reorganized_locations.merge(aux_df, how='left', left_on=parentlocid, right_on=parentlocid)
            self.reorganized_locations.dropna('columns', how='all', inplace=True)
            return self.reorganized_locations

        except Exception as e:
            QgsMessageLog.logMessage(f'{e}', level=Qgis.Info)

    def update_date_fields(self, df):
        date_flds = ['date', 'dateOfReporting', 'dateOfOnset', 'dateOfInfection', 'dateOfLastContact', 
                    'dateBecomeCase', 'dateOfOutcome', 'dateFollowUpStart' , 'dateFollowUpEnd', 'dateOfBurial']
        dt_flds = ['createdAt', 'updatedAt']
        for fld in date_flds:
            try:
                df[fld] = df[fld].str.split('T').str[0]
            except:
                pass
        for fld in dt_flds:
            try:
                df[fld] = df[fld].astype('datetime64[s]')
            except:
                pass

    def fieldValueSplitter(self, df, field, splitter, idx= -1):
        if field in df.columns:
            if df[field].isnull().all():
                pass
            else:
                df[field] = df[field].str.split(splitter).str[idx]

    def clean_ref_data(self, df):
        self.fieldValueSplitter(df, 'gender', 'GENDER_')
        self.fieldValueSplitter(df, 'classification', 'CLASSIFICATION_')
        self.fieldValueSplitter(df, 'riskLevel', 'RISK_LEVEL_')        
        self.fieldValueSplitter(df, 'locationClassification', 'ADDRESS_TYPE_')        
        self.fieldValueSplitter(df, 'outcomeId', 'OUTCOME_')     
        self.fieldValueSplitter(df, 'pregnancyStatus', 'PREGNANCY_STATUS_')           
        self.fieldValueSplitter(df, 'occupation', 'OCCUPATION_')
    
    def get_age_groups(self, df):
        age_bins = [-1, 4, 14, 24, 64, 150]
        age_labels = ['<5 years', '5-14 years', '15-24 years', '25-64 years', '65+ years']
        if 'age_years' in df.columns:
            df['ageClass'] = pd.cut(df['age_years'], bins=age_bins, labels=age_labels)
    
    def summarize_cases(self, df):
        try:
            df.loc[df['dateOfReporting']==self.yesterday.strftime('%Y-%m-%d'), 'Daily New Confirmed']=1
        except:
            df['Daily New Confirmed'] = 0

        try:
            df.loc[(df['dateOfReporting']<=self.yesterday.strftime('%Y-%m-%d')) 
                & (df['dateOfReporting']>= self.fourteen_days_ago.strftime('%Y-%m-%d')), 'Confirmed Last Fourteen']=1
        except:
            df['Confirmed Last Fourteen'] = 0

        try:
            df.loc[(df['dateOfReporting']<=self.yesterday.strftime('%Y-%m-%d')) 
                & (df['dateOfReporting']>=self.twenty_eight_days_ago.strftime('%Y-%m-%d')), 'Confirmed Last Twenty Eight']=1
        except:
            df['Confirmed Last Twenty Eight'] = 0
            
        try:
            df.loc[(df['dateOfReporting']<=self.yesterday.strftime('%Y-%m-%d')) 
                & (df['dateOfReporting']>=self.seven_days_ago.strftime('%Y-%m-%d')), 'Confirmed Last Seven']=1
        except:
            df['Confirmed Last Seven'] = 0


        df['Total Count'] = 1

        summary_cases = df.groupby([f'admin_{self.admin_level}_name', self.tabular_join_field]).sum()[['Daily New Confirmed','Confirmed Last Seven','Confirmed Last Fourteen','Confirmed Last Twenty Eight','Total Count']]

        summary_cases.to_csv(f'{self.in_gd_output_path}/{self.out_summary_data}.csv', encoding='utf-8-sig')