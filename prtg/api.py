import re
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from prtg.icon import Icon
from prtg.exception import DuplicateObject, ObjectNotFound, Unauthorized

class PrtgApi:
    """Class to communicate with PRTG instance using PRTG API.
    Validates credentials on __init__.

    Attributes:
        id_pattern (re.Pattern): (class attribute) regex pattern to find object 
            ID from response URL
        url (str): instance of PRTG
        username (str): username credential needed for API
        password (str): password (or pashash) credential needed for API
        is_passhash (bool, optional): specify if using passhash or password. 
            Defaults to False.
    """
    id_pattern = re.compile('(?<=(\?|&)id=)\d+')

    def __init__(self, 
            url, 
            username, 
            password, 
            is_passhash = False,
            requests_verify = True):
        self.url = url
        self.username = username
        self.password = password
        self.is_passhash = is_passhash
        self.requests_verify = requests_verify
        self._validate_cred()
    
    def _requests_get(self, endpoint, params={}):
        """Wraps function `requests.get` to add credentials
        to parameter and capture specific response error codes.

        Args:
            endpoint (str): API endpoint (not including base url)
            params (dict, optional): any additional params. Defaults to None.

        Raises:
            Unauthorized: when lacking or having invalid credentials
            requests.HTTPError: when client or server side errors. Re-prints 
            error status codes 400 and 404 for clarity

        Returns:
            requests.Resposne: response of GET API
        """
        url = self.url + endpoint
        key = 'passhash' if self.is_passhash else 'password'
        auth = {'username': self.username, key: self.password}
        # attach additional parameters
        auth.update(params)
        response = requests.get(url, auth, verify=self.requests_verify)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code == 400:
                root = ET.fromstring(response.text)
                error_msg = root.find('error').text
                raise requests.HTTPError(error_msg)
            elif response.status_code == 401:
                raise Unauthorized('Authentication failed for PRTG API.')
            elif response.status_code == 404:
                raise requests.HTTPError('Content not found.')
            raise requests.HTTPError(e)
        return response

    def _requests_post(self, endpoint, params={}, data={}):
        """Wraps function `requests.post` to add credentials
        to parameter and capture specific response error codes.

        Args:
            endpoint (str): API endpoint (not including base url)
            params (dict, optional): any additional params. Defaults to None.
            data (dict, optional): form-encoded data to send. Defaults to None.

        Returns:
            requests.Resposne: response of POST API
        """
        url = self.url + endpoint
        key = 'passhash' if self.is_passhash else 'password'
        auth = {'username': self.username, key: self.password}
        auth.update(params)
        response = requests.post(url, data, params=auth, verify=self.requests_verify)
        response.raise_for_status()
        return response

    def _validate_cred(self):
        """Validate credentials
        """  
        self._requests_get('/api/healthstatus.json')

    def _parse_obj_id(self, url):
        """Helper function to extract ID from response URL

        Args:
            url (str): response URL

        Returns:
            int: id of object
        """
        return int(PrtgApi.id_pattern.search(urllib.parse.unquote(url), re.I).
        group(0))

    def device_url(self, id):
        """Creates URL of device.

        Args:
            id (Union[int, str]): id of device

        Returns:
            str: URL of device
        """
        return f'{self.url}/device.htm?id={id}'

    # Sensortree

    def get_sensortree(self, group_id=None):
        """Get sensortree

        Args:
            group_id (Union[int, str], optional): Group id of desired root. Defaults to None.

        Returns:
            str: XML structure of sensortree
        """
        endpoint = '/api/table.xml'
        params = {
            'content': 'sensortree',
            'id': group_id
        }
        response = self._requests_get(endpoint, params)
        return response.text

    # Probes

    def _get_probes_base(self, extra=None):
        """Base function for returning probes

        Args:
            extra (dict): additional parameters to filter probes. Defaults to 
                None.

        Returns:
            list[dict]: probes and their details
        """
        endpoint = '/api/table.json'
        params = {
            'content': 'probes',
            'filter_parentid': 0,
            'columns': 'objid,name,active,tags,parentid,priority,\
                        status,groupnum,devicenum,location'
        }
        if extra:
            params.update(extra)
        response = self._requests_get(endpoint, params)
        return response.json()['probes']

    def get_all_probes(self):
        """Get all probes

        Returns:
            list[dict]: all probes and their details
        """
        return self._get_probes_base()

    def get_probe_by_name(self, name):
        """Get one probe by name

        Args:
            name (str): name of probe

        Raises:
            DuplicateObject: when more than one probe is found
            ObjectNotFound: when no probe is found

        Returns:
            dict: probe details
        """
        params = {'filter_name': name}
        result = self._get_probes_base(params)
        if len(result) > 1:
            raise DuplicateObject('Multiple probes with same name.')
        try:
            return result[0]
        except IndexError:
            raise ObjectNotFound('No probe with matching name.')

    def get_probe(self, id):
        """Get one probe by id

        Args:
            id (Union[int, str]): id of probe

        Raises:
            ObjectNotFound: when no probe is found

        Returns:
            dict: probe details
        """
        params = {'filter_objid':id}
        try:
            return self._get_probes_base(params)[0]
        except IndexError:
            raise ObjectNotFound('No probe with matching ID.')

    # Groups

    def _get_groups_base(self, extra=None):
        """Base function for returning groups

        Args:
            extra (dict): additional parameters to filter groups. Defaults to 
                None.

        Returns:
            list[dict]: groups and their details
        """
        endpoint = '/api/table.json'
        params = {
            'content': 'groups',
            'columns': 'objid,name,active,status,probe,priority,\
                        tags,location,parentid,groupnum,devicenum'
        }
        if extra:
            params.update(extra)
        response = self._requests_get(endpoint, params)
        return response.json()['groups']

    def get_all_groups(self):
        """Get all groups

        Returns:
            list[dict]: all groups and their details
        """
        return self._get_groups_base()

    def get_groups_by_name_containing(self, name):
        """Get groups by name

        Args:
            name (str): name of group

        Returns:
            list[dict]: list of groups and their details
        """
        params = {'filter_name': f'@sub({name})'}
        return self._get_groups_base(params)

    def get_group_by_name(self, name):
        """Get one group by name. *Note currently having issues with retrieving 
        names containing '[]', consider using get_groups_by_name_containing() 
        instead

        Args:
            name (str): name of group

        Raises:
            DuplicateObject: when more than one group is found
            ObjectNotFound: when no group is found

        Returns:
            dict: group details
        """
        params = {'filter_name': name}
        result = self._get_groups_base(params)
        if len(result) > 1:
            raise DuplicateObject('Multiple groups with same name.')
        try:
            return result[0]
        except IndexError:
            raise ObjectNotFound('No group with matching name.')

    def get_group(self, id):
        """Get one group by id

        Args:
            id (Union[int, str]): id of group

        Raises:
            ObjectNotFound: when no group is found

        Returns:
            dict: group details
        """
        params = {'filter_objid': id}
        try:
            return self._get_groups_base(params)[0]
        except IndexError:
            raise ObjectNotFound('No group with matching ID.')

    def add_group(self, name, group_id):
        """Add new group. For simpliciy, this function is limited in 
        customizing the group. Use set property functions to edit other 
        properties. *This is not officially a part of the API so there will be 
        some uniqueness. 

        Args:
            name (str): name of new group
            group_id (Union[int, str]): id of parent group

        Returns:
            dict: group details
            None: failed to create group
        """
        # get duplicate groups first to differentiate later
        duplicate_groups = self.get_groups_by_name_containing(name)

        endpoint = '/addgroup2.htm'
        data = {
            'id': group_id,
            'name_': name
        }
        
        # unsupported API so no proper response to catch
        self._requests_post(endpoint, data=data)
        
        # find difference to get group
        groups = self.get_groups_by_name_containing(name)
        group = [x for x in groups if x not in duplicate_groups]
        try:
            return group[0]
        except IndexError:
            # failed to create group
            return None

    def clone_group(self, name, group_id, clone_id):
        """Clone new group

        Args:
            name (str): name of new group
            group_id (Union[int, str]): id of parent group

        Returns:
            str: id of new group
        """
        endpoint = '/api/duplicateobject.htm'
        params = {
            'id': clone_id,
            'name': name,
            'targetid': group_id
        }
        response = self._requests_get(endpoint, params)
        return self._parse_obj_id(response.url)

    # Devices

    def _get_devices_base(self, extra={}):
        """Base function for returning devices

        Args:
            extra (dict): additional parameters to filter devices. Defaults to 
                None.

        Returns:
            list[dict]: devices and their details
        """
        endpoint = '/api/table.json'
        params = {
            'content': 'devices',
            'columns': 'objid,name,active,status,probe,group,host,\
                        priority,tags,location,parentid,icon'
        }
        params.update(extra)
        response = self._requests_get(endpoint, params)
        return response.json()['devices']

    def get_all_devices(self):
        """Get all devices

        Returns:
            list[dict]: all devices and their details
        """
        return self._get_devices_base()

    def get_devices_by_group_id(self, group_id):
        """Get devices by parent group

        Args:
            group_id (Union[int, str]): id of parent group

        Returns:
            list[dict]: devices and their details
        """
        params = {'id': group_id}
        return self._get_devices_base(params)

    def get_devices_by_name_containing(self, name):
        """Get devices by partial or full name

        Args:
            name (str): partial or full name

        Returns:
            list[dict]: devices and their details
        """
        params = {'filter_name': f'@sub({name})'}
        return self._get_devices_base(params)

    def get_device_by_name(self, name):
        """Get one device by name

        Args:
            name (str): name of device

        Raises:
            DuplicateObject: when more than one device is found
            ObjectNotFound: when no device is found

        Returns:
            dict: device details
        """
        params = {'filter_name': name}
        result = self._get_devices_base(params)
        if len(result) > 1:
            raise DuplicateObject('Multiple devices with same name.')
        try:
            return result[0]
        except IndexError:
            raise ObjectNotFound('No device with matching name.')

    def get_device(self, id):
        """Get one device by id

        Args:
            id (Union[int, str]): id of device

        Raises:
            ObjectNotFound: when no device is found

        Returns:
            dict: device details
        """
        params = {'filter_objid': id}
        try:
            return self._get_devices_base(params)[0]
        except IndexError:
            raise ObjectNotFound('No device with matching ID.')

    def add_device(self, name, host, group_id, icon=Icon.SERVER):
        """Add new device. For simpliciy, this function is limited in 
        customizing the device. Use set property functions to edit other 
        properties. *This is not officially a part of the API so there will be 
        some uniqueness. 

        Args:
            name (str): name of new device
            host (str): hostname or IP address of device
            group_id (Union[int, str]): id of parent group
            icon (Icon): icon of device
        """
        # get duplicate devices first to differentiate later
        duplicate_devices = self.get_devices_by_name_containing(name)

        endpoint = '/adddevice2.htm'
        data = {
            'id': group_id,
            'name_': name,
            'host_': host,
            'deviceicon_': icon.value
        }

        # unsupported API so no proper response to catch
        self._requests_post(endpoint, data=data)
        
        # find difference to get device
        devices = self.get_devices_by_name_containing(name)
        device = [x for x in devices if x not in duplicate_devices]
        try:
            return device[0]
        except IndexError:
            # failed to create device
            return None

    def clone_device(self, name, host, group_id, clone_id):
        """Clone new device

        Args:
            name (str): name of new device
            host (str): hostname or IP address of device
            group_id (Union[int, str]): id of parent group

        Returns:
            str: id of new device
        """
        endpoint = '/api/duplicateobject.htm'
        params = {
            'id': clone_id,
            'name': name,
            'host': host,
            'targetid': group_id
        }
        response = self._requests_get(endpoint, params)
        return self._parse_obj_id(response.url)

    # Object Status

    def _get_obj_status_base(self, id, status):
        """Base function for returning object statuses

        Args:
            id (Union[int, str]): id of object
            status (str): name of status

        Returns:
            str: value of status
        """
        endpoint = '/api/getobjectstatus.htm'
        params = {
            'id': id,
            'name': property,
            'show': 'nohtmlencode'
        }
        response = self._requests_get(endpoint, params)
        root = ET.fromstring(response.text)
        return root.find('result').text

    # Object Property

    def _get_obj_property_base(self, id, property):
        """Base function for returning object properties

        Args:
            id (Union[int, str]): id of object
            property (str): name of property

        Returns:
            str: value of property
        """
        endpoint = '/api/getobjectproperty.htm'
        params = {
            'id': id,
            'name': property,
            'show': 'nohtmlencode'
        }
        response = self._requests_get(endpoint, params)
        tree = ET.fromstring(response.content)
        return tree.find('result').text

    def get_hostname(self, id):
        """Get hostname of object

        Args:
            id (Union[int, str]): id of object

        Returns:
            str: hostname of object
        """
        return self._get_obj_property_base(id, 'host')

    def get_service_url(self, id):
        """Get service URL of object

        Args:
            id (Union[int, str]): id of object

        Returns:
            str: service URL of object
        """
        return self._get_obj_property_base(id, 'serviceurl')

    def _set_obj_property_base(self, id, name, value):
        """Base function for setting object properties

        Args:
            id (Union[int, str]): id of object
            name (str): name of property
            value (str): value of property
        """
        endpoint = '/api/setobjectproperty.htm'
        params = {
            'id': id,
            'name': name,
            'value': value
        }
        self._requests_get(endpoint, params)

    def set_hostname(self, id, host):
        """Set hostname of object

        Args:
            id (Union[int, str]): id of object
            host (str): hostname or IP address
        """
        self._set_obj_property_base(id, 'host', host)

    def set_icon(self, id, icon):
        """Set icon of object

        Args:
            id (Union[int, str]): id of object
            icon (Icon): icon to set
        """
        self._set_obj_property_base(id, 'deviceicon', icon.value)

    def set_location(self, id, location):
        """Set location of object

        Args:
            id (Union[int, str]): id of object
            location (str): location to set
        """
        self._set_obj_property_base(id, 'location', location)

    def set_service_url(self, id, url):
        """Set service URL of object

        Args:
            id (Union[int, str]): id of object
            url (str): service URL to set
        """
        self._set_obj_property_base(id, 'serviceurl', url)

    def set_tags(self, id, tags):
        """Set new tags for object.

        Args:
            id (Union[int, str]): id of object
            tags (list[str]): tags to set
        """
        # api accepts each space-separated word as a tag so
        # replace spaces in each tag and then combine with spaces
        combined_tags = ' '.join([tag.replace(' ', '-') for tag in tags])
        self._set_obj_property_base(id, 'tags', combined_tags)

    def set_inherit_location_off(self, id):
        """Turn off location inheritance setting of object

        Args:
            id (Union[int, str]): id of object
        """
        self._set_obj_property_base(id, 'locationgroup_', 0)

    def set_inherit_location_on(self, id):
        """Turn on location inheritance setting of object

        Args:
            id (Union[int, str]): id of object
        """
        self._set_obj_property_base(id, 'locationgroup_', 1)

    # Sensors

    def _get_sensors_base(self, extra=None):
        """Base function for returning sensors

        Args:
            extra (dict): additional parameters to filter sensors. Defaults to 
                None.

        Returns:
            list[dict]: sensors and their details
        """
        endpoint = '/api/table.json'
        params = {
            'content': 'sensors',
            'columns': 'objid,probe,group,device,status,priority,active,name'
        }
        if extra:
            params.update(extra)
        response = self._requests_get(endpoint, params)
        return response.json()['sensors']
        
    def get_sensors_by_name(self, name, group=None, device=None):
        """Get sensors by name

        Args:
            name (str): name of sensor
            group (str, optional): name of group to filter by. Defaults to None.
            device (str, optional): name of device to filter by. Defaults to None.

        Returns:
            list[dict]: sensors and their details
        """
        params = {
            'filter_name': name,
            'filter_device': device
        }
        if group:
            params['filter_group']= f'@sub({group})'
        return self._get_sensors_base(params)

    def get_sensors_by_name_containing(self, name, group=None, device=None):
        """Get sensors by partial or full name

        Args:
            name (str): partial or full name of sensor
            group (str, optional): name of group to filter by. Defaults to None.
            device (str, optional): name of device to filter by. Defaults to None.

        Returns:
            list[dict]: sensors and their details
        """
        params = {
            'filter_name': f'@sub({name})',
            'filter_device': device
        }
        if group:
            params['filter_group']= f'@sub({group})'
        return self._get_sensors_base(params)

    def get_sensor(self, id):
        """Get one sensor by id

        Args:
            id (Union[int, str]): id of sensor

        Raises:
            ObjectNotFound: when no sensor is found

        Returns:
            dict: sensor details
        """
        params = {'filter_objid': id}
        try:
            return self._get_sensors_base(params)[0]
        except IndexError:
            raise ObjectNotFound('No sensor with matching ID.')

    # Actions

    def move_object(self, id, group_id):
        """Move object to new group

        Args:
            id (Union[int, str]): id of object
            group_id (Union[int, str]): id of target group
        """
        endpoint = '/moveobjectnow.htm'
        params = {
            'id': id,
            'targetid': group_id
        }
        self._requests_get(endpoint, params)

    def pause_object(self, id):
        """Pause object

        Args:
            id (Union[int, str]): id of object
        """
        endpoint = '/api/pause.htm'
        params = {
            'id': id,
            'action': 0
        }
        self._requests_get(endpoint, params)

    def resume_object(self, id):
        """Resume object

        Args:
            id (Union[int, str]): id of object
        """
        endpoint = '/api/pause.htm'
        params = {
            'id': id,
            'action': 1
        }
        self._requests_get(endpoint, params)

    def delete_object(self, id):
        """Delete object

        Args:
            id (Union[int, str]): id of object
        """
        endpoint = '/api/deleteobject.htm'
        params = {
            'id': id,
            'approve': 1
        }
        self._requests_get(endpoint, params)

    def set_priority(self, id, value):
        """Set priority of object

        Args:
            id (Union[int, str]): id of object
            value (Union[int, str]): priority number

        Raises:
            ValueError: when value is outside range 1-5
        """
        if value < 1 or value > 5:
            raise ValueError('Priorty can only set between 1 - 5.')
        endpoint = '/api/setpriority.htm'
        params = {
            'id': id,
            'prio': value
        }
        self._requests_get(endpoint, params)
