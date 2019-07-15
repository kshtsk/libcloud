# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import time

from libcloud.common.gridscale import GridscaleBaseDriver
from libcloud.common.gridscale import GridscaleConnection
from libcloud.compute.base import NodeImage, NodeLocation, VolumeSnapshot, \
    Node, StorageVolume, KeyPair, NodeState, StorageVolumeState
from libcloud.compute.providers import Provider
from libcloud.utils.iso8601 import parse_date


class GridscaleIp(object):
    """
    Ip Object

    :param id: uuid
    :type id: ``str``
    :param family: family of ip (v4 or v6)
    :type family: ``str``
    :param prefix: prefix of ip
    :type prefix: ``str``
    :param ip_address: Ip address
    :type ip_address: ``str``
    :param create_time: Time ip was created
    :type create_time: ``str``
    """

    def __init__(self, id, family, prefix, create_time, address):
        self.id = id
        self.family = family
        self.prefix = prefix
        self.create_time = create_time
        self.ip_address = address

    def __repr__(self):
        return ('Ip: id={}, family={}, prefix={}, create_time={},Ip_address={}'
                .format(self.id, self.family,
                        self.prefix,
                        self.create_time,
                        self.ip_address))


class GridscaleNetwork(object):
    """
    Network Object

    :param id: uuid
    :type id: ``str``
    :param name: Name of Network
    :type name: ``str``
    :param status: Network status
    :type status: ``str``
    :param relations: object related to network
    :type relations: ``object``
    :param create_time: Time Network was created
    :type create_time: ``str``
    """

    def __init__(self, id, name, status, create_time, relations):
        self.id = id
        self.name = name
        self.status = status
        self.create_time = create_time
        self.relations = relations

    def __repr__(self):
        return ('Network: id={}, name={}, status={}, create_time={}, '
                'relations={}'.format(self.id, self.name, self.status,
                                      self.create_time, self.relations))


class GridscaleNodeDriver(GridscaleBaseDriver):
    """
    create and entry in libcloud/compute/providers for gridscale
    """
    connectionCls = GridscaleConnection
    type = Provider.GRIDSCALE
    name = 'gridscale'
    website = 'https://gridscale.io'

    def __init__(self, user_id, key, **kwargs):
        super(GridscaleNodeDriver, self).__init__(user_id, key, **kwargs)

    def list_nodes(self):
        """
        List all nodes.

        :return: List of node objects
        :rtype: ``list`` of :class:`.Node`
        """
        result = self._sync_request(data=None, endpoint='objects/servers/')
        nodes = []
        for key, value in self._get_response_dict(result).items():
            node = self._to_node(value)
            nodes.append(node)
            continue

        return sorted(nodes, key=lambda sort: sort.created_at)

    def list_locations(self):
        """
        List all available data centers.

        :return: List of node location objects
        :rtype: ``list`` of :class:`.NodeLocation`
        """
        locations = []
        result = self._sync_request(endpoint='objects/locations/')
        for key, value in self._get_response_dict(result).items():
            location = self._to_location(value)
            locations.append(location)
            continue
        return sorted(locations, key=lambda nod: nod.id)

    def list_volumes(self):
        """
        List all volumes.

        :return: List of StorageVolume object
        :rtype: ``list`` of :class:`.StorageVolume`
        """
        volumes = []
        result = self._sync_request(endpoint='objects/storages/')
        for key, value in self._get_response_dict(result).items():
            volume = self._to_volume(value)
            volumes.append(volume)
        return sorted(volumes, key=lambda sort: sort.extra['create_time'])

    def ex_list_networks(self):
        """
        List all networks.

        :return: List of objects.
        :rtype: ``list`` of :class:`.GridscaleNetwork`
        """
        networks = []
        result = self._sync_request(endpoint='objects/networks/')
        for key, value in self._get_response_dict(result).items():
            network = self._to_network(value)
            networks.append(network)
        return sorted(networks, key=lambda sort: sort.create_time)

    def list_volume_snapshots(self, volume):
        """
        Lists all snapshots for storage volume.

        :param volume: storage the snapshot is attached to
        :type volume: :class:`.StorageVolume`

        :return: Snapshots
        :rtype: ``list`` of :class:`.VolumeSnapshot`
        """
        snapshots = []
        result = self._sync_request(
            endpoint='objects/storages/'
                     '{}/snapshots'.format(volume.id))
        for key, value in self._get_response_dict(result).items():
            snapshot = self._to_volume_snapshot(value)
            snapshots.append(snapshot)
        return sorted(snapshots, key=lambda snapshot: snapshot.created)

    def ex_list_ips(self):
        """
        Lists all IPs available.

        :return: List of IP objects.
        :rtype: ``list`` of :class:`.GridscaleIp`
        """
        ips = []
        result = self._sync_request(endpoint='objects/ips/')
        for key, value in self._get_response_dict(result).items():
            ip = self._to_ip(value)
            ips.append(ip)
        return ips

    def list_images(self):
        """
        List images.

        :return: List of node image objects
        :rtype: ``list`` of :class:`.NodeImage`
        """
        templates = []
        result = self._sync_request(endpoint='objects/templates')
        for key, value in self._get_response_dict(result).items():
            template = self._to_node_image(value)
            templates.append(template)
        return sorted(templates, key=lambda sort: sort.name)

    def create_node(self, name, size, image, location, ex_ssh_key_ids=None):
        """
        Create a simple node  with a name, cores, memory at the designated
        location.

        :param name: Name of the server.
        :type name: ``str``

        :param size: Nodesize object.
        :type size: :class:`.NodeSize`

        :param image: OS image to attach to the storage.
        :type image: :class:`.GridscaleTemplate`

        :param location: The data center to create a node in.
        :type location: :class:`.NodeLocation`

        :keyword ex_ssh_key_ids: sshkey uuid.
        :type ex_ssh_key_ids: ``str``

        :return: The newly created Node.
        :rtype: :class:`.Node`

        """

        if size.ram % 1024 != 0:
            raise Exception('Value not accepted. Use a multiple of 1024 e.g.'
                            '1024, 2048, 3096...')
        data = {
            'name': name,
            'cores': size.extra['cores'],
            'memory': int(size.ram / 1024),
            'location_uuid':
                location.id}
        self.connection.async_request('objects/servers/',
                                      data=json.dumps(data),
                                      method='POST')

        node = self._to_node(self._get_resource('servers', self.connection
                                                .poll_response_initial
                                                .object['object_uuid']))

        volume = self._create_volume_from_template(name=image.extra['ostype'],
                                                   size=size.disk,
                                                   location=location,
                                                   template={
                                                   'template_uuid': image.id,
                                                   'sshkeys': ex_ssh_key_ids})

        ip = self.ex_create_ip(4, location, name + '_ip')

        self.attach_volume(node, volume)
        self.ex_link_ip_to_node(node, ip)
        self.ex_link_network_to_node(node, self.ex_list_networks()[0])
        self.ex_start_node(node)

        return self._to_node(self._get_resource('servers', node.id))

    def ex_create_ip(self, family, location, name):
        """
        Create either an ip_v4 ip or a ip_v6.

        :param family: Defines if the ip is v4 or v6 with int 4 or int 6.
        :type family: ``int``

        :param location: Defines which datacenter the created ip
                         responds with.
        :type location: :class:`.NodeLocation`

        :param name: Name of your Ip.
        :type name: ``str``

        :return: Ip
        :rtype: :class:`.GridscaleIp`
        """
        self.connection.async_request(
            'objects/ips/',
            data=json.dumps({
                'name': name,
                'family': family,
                'location_uuid': location.id}),
            method='POST')

        return self._to_ip(self._get_resource('ips', self.connection
                                              .poll_response_initial
                                              .object['object_uuid']))

    def ex_create_networks(self, name, location):
        """
        Create a network at the data center location.

        :param name: Name of the network.
        :type name: ``str``

        :param location: Location.
        :type location: :class:`.NodeLocation`

        :return: Network.
        :rtype: :class:`.GridscaleNetwork`
        """
        self.connection.async_request(
            'objects/networks',
            data=json.dumps({
                'name': name,
                'location_uuid': location.id}),
            method='POST')

        return self._to_network(self._get_resource('network', self.connection
                                                   .poll_response_initial
                                                   .object['object_uuid']))

    def create_volume(self, size, name, location=None, snapshot=None):
        """
        Create a new volume.

        :param size: Integer in GB.
        :type size: ``int``

        :param name: Name of the volume.
        :type name: ``str``

        :param location: The server location.
        :type location: :class:`.NodeLocation`

        :param snapshot:  Snapshot from which to create the new
                          volume.  (optional)
        :type snapshot: :class:`.VolumeSnapshot`

        :return: Newly created StorageVolume.
        :rtype: :class:`.StorageVolume`
        """

        return self._create_volume_from_template(size, name, location)

    def _create_volume_from_template(self, size, name, location=None,
                                     template={}):
        """
        create Storage

        :param name: name of your Storage unit
        :type name: ``str``

        :param size: Integer in GB.
        :type size: ``int``

        :param location: your server location
        :type location: :class:`.NodeLocation`

        :param template: template to shape the storage capacity to
        :type template: ``dict``

        :return: newly created StorageVolume
        :rtype: :class:`.GridscaleVolumeStorage`
        """
        self.connection.async_request(
            'objects/storages/',
            data=json.dumps({
                'name': name,
                'capacity': size,
                'location_uuid': location.id,
                'template': template}),
            method='POST')

        return self._to_volume(self._get_resource('storages',
                                                  self.connection
                                                  .poll_response_initial
                                                  .object['object_uuid']))

    def create_volume_snapshot(self, volume, name):
        """
        Creates a snapshot of the current state of your volume,
        you can rollback to.

        :param volume: Volume you want to create a snapshot of.
        :type volume: :class:`.StorageVolume`

        :param name: Name of the snapshot.
        :type name: ``str``

        :return: VolumeSnapshot.
        :rtype: :class:`.VolumeSnapshot`
        """
        self.connection.async_request(
            'objects/storages/{}/snapshots'.format(volume.id),
            data=json.dumps({
                'name': name}),
            method='POST')

        return self._to_volume_snapshot(self._get_resource(
            'storages/{}/snapshots'.format(volume.id), self.connection
            .poll_response_initial.object['object_uuid']))

    def create_image(self, node, name):
        """
        Creates an image from a node object.

        :param node: Node to run the task on.
        :type node: :class:`.Node`

        :param name: Name for new image.
        :type name: ``str``

        :return: NodeImage.
        :rtype: :class:`.NodeImage`
        """
        storage_dict = node.extra['relations']['storages'][0]
        snapshot_uuid = ''
        if storage_dict['bootdevice'] is True:
            self.connection.async_request(
                'objects/storages/{}/snapshots/'
                .format(storage_dict['object_uuid']),
                data=json.dumps({'name': name + '_snapshot'}),
                method='POST')

            snapshot_uuid = self.connection.poll_response_initial.object[
                'object_uuid']

            self.connection.async_request(
                'objects/templates/',
                data=json.dumps({
                    'name': name,
                    'snapshot_uuid': snapshot_uuid}),
                method='POST')

            snapshot_dict = self._get_response_dict(self._sync_request(
                endpoint='objects/storages/{}/snapshots/{}'
                .format(storage_dict['object_uuid'], snapshot_uuid)))

            self.destroy_volume_snapshot(
                self._to_volume_snapshot(snapshot_dict))

        return self._to_node_image(self._get_resource(
            'templates', self.connection.poll_response_initial.object[
                'object_uuid']))

    def destroy_node(self, node):
        """
        Destroy node.

        :param node: Node object.
        :type node: :class:`.Node`

        :return: True if the destroy was successful, otherwise False.
        :rtype: ``bool``
        """
        result = self._sync_request(endpoint='objects/servers/{}'
                                    .format(node.id),
                                    method='DELETE')
        return result.status == 204

    def destroy_volume(self, volume):
        """
        Delete volume.

        :param volume: Volume to be destroyed.
        :type volume: :class:`.StorageVolume`

        :return: True if the destroy was successful, otherwise False.
        :rtype: ``bool``
        """
        result = self._sync_request(endpoint='objects/storages/{}'
                                    .format(volume.id),
                                    method='DELETE')
        return result.status == 204

    def ex_destroy_ip(self, ip):
        """
        Delete an ip.

        :param ip: IP object.
        :type ip: :class:`.GridscaleIp`

        :return: ``True`` if delete_image was successful, ``False`` otherwise.
        :rtype: ``bool``
        """
        result = self._sync_request(endpoint='objects/ips/{}'
                                    .format(ip.id),
                                    method='DELETE')
        return result.status == 204

    def destroy_volume_snapshot(self, snapshot):
        """
        Destroy a snapshot.

        :param snapshot: The snapshot to delete.
        :type snapshot: :class:'.VolumeSnapshot`

        :return: True if the destroy was successful, otherwise False.
        :rtype: ``bool``
        """
        result = self._sync_request(endpoint='objects/storages/'
                                             '{}/snapshots/{}/'
                                    .format(snapshot.extra['parent_uuid'],
                                            snapshot.id),
                                    method='DELETE')
        return result.status == 204

    def ex_destroy_networks(self, network):
        """
        Delete network.

        :param network: Network object.
        :type network: :class:`.GridscaleNetwork`

        :return: ``True`` if destroyed successfully, otherwise ``False``
        :rtype: ``bool``
        """
        result = self._sync_request(endpoint='objects/networks/{}'
                                    .format(network.id),
                                    method='DELETE')
        return result.status == 204

    def delete_image(self, node_image):
        """
        Destroy an image.

        :param node_image: Node image object.
        :type node_image: :class:`.NodeImage`

        :return: True if the destroy was successful, otherwise False
        :rtype: ``bool``

        """
        result = self._sync_request(endpoint='objects/templates/{}'
                                    .format(node_image.id),
                                    method='DELETE')
        return result.status == 204

    def ex_rename_node(self, node, name=None):
        """
        Modify node name.

        :param name: New node name.
        :type name: ``str``

        :param node: Node
        :type node: :class:`.Node`

        :return: ``True`` or ``False``
        :rtype: ``bool``
        """
        result = self._sync_request(data=json.dumps({'name': name}),
                                    endpoint='objects/servers/{}'
                                    .format(node.id),
                                    method='PATCH')
        return result.status == 204

    def ex_rename_storage(self, storage, name=None):
        """
        Modify storage name

        :param storage: Storage.
        :type storage: :class:.`StorageVolume`

        :param name: New storage name.
        :type name: ``str``

        :return: ``True`` or ``False``
        :rtype: ``bool``
        """
        result = self._sync_request(data=json.dumps({'name': name}),
                                    endpoint='objects/servers/{}'
                                    .format(storage.id),
                                    method='PATCH')
        return result.status == 204

    def ex_rename_network(self, network, name=None):
        """
        Modify networks name.

        :param network: Network.
        :type network: :class:`.GridscaleNetwork`

        :param name: New network name.
        :type name: ``str``

        :return: ``True`` or ``False``
        :rtype: ``bool``
        """
        result = self._sync_request(data=json.dumps({'name': name}),
                                    endpoint='objects/networks/{}'
                                    .format(network.id),
                                    method='PATCH')
        return result.status == 204

    def reboot_node(self, node):
        """
        Reboot a node.

        :param node: Node object.
        :type node: :class:`.Node`

        :return: True if the reboot was successful, otherwise False.
        :rtype: ``bool``

        """

        if node.extra['power'] is True:
            data = dict({'power': False})
            self._sync_request(data=json.dumps(data),
                               endpoint='objects/servers/{}/power'
                               .format(node.id),
                               method='PATCH')
            time.sleep(3)

            data = dict({'power': True})
            self._sync_request(data=json.dumps(data),
                               endpoint='objects/servers/{}/power'
                               .format(node.id),
                               method='PATCH')
            return True

        else:

            return False

    def list_key_pairs(self):
        """
        List all the available key pair objects.

        :rtype: ``list``of :class:`.KeyPair` objects
        """
        keys = []
        result = self._sync_request(endpoint='objects/sshkeys/')
        for key, value in self._get_response_dict(result).items():
            key = self._to_key(value)
            keys.append(key)
        return keys

    def get_image(self, image_id):
        """
        Get an image based on an image_id.

        :param image_id: Image identifier.
        :type image_id: ``str``

        :return: A NodeImage object.
        :rtype: :class:`.NodeImage`
        """

        response_dict = self._get_response_dict(self._sync_request(
                                                endpoint='/objects/templates/{}'
                                                         .format(image_id)))

        return self._to_node_image(response_dict)

    def ex_start_node(self, node):

        result = self._sync_request(data=json.dumps({'power': True}),
                                    endpoint='objects/servers/{}/power'
                                    .format(node.id),
                                    method='PATCH')

        return result.status == 204

    def ex_link_isoimage_to_node(self, node, isoimage):
        """
        link and isoimage to a node

        :param node: Node you want to link the iso image to
        :type node: ``object``

        :param isoimage: isomiage you want to link
        :type isoimage: ``object``

        :return: None -> success
        :rtype: ``None``
        """
        result = self._sync_request(data=json.dumps({'object_uuid':
                                                    isoimage.id}),
                                    endpoint='objects/servers/{}/isoimages/'
                                    .format(node.id),
                                    method='POST')
        return result

    def attach_volume(self, node, volume):
        """
         Attaches volume to node.

        :param node: Node to attach volume to.
        :type node: :class:`.Node`

        :param volume: Volume to attach.
        :type volume: :class:`.StorageVolume`

        :rytpe: ``bool``
        """
        result = self._sync_request(data=json.dumps({'object_uuid':
                                                    volume.id}),
                                    endpoint='objects/servers/{}/storages/'
                                    .format(node.id),
                                    method='POST')
        return result.status == 204

    def ex_link_network_to_node(self, node, network):
        """
        Link a network to a node.

        :param node: Node object to link networks to.
        :type node: :class:`.Node`

        :param network: Network you want to link.
        :type network: :class:`.GridscaleNetwork`

        :return: ``True`` if linked sucessfully, otherwise ``False``
        :rtype: ``bool``
        """
        result = self._sync_request(data=json.dumps({'object_uuid':
                                                    network.id}),
                                    endpoint='objects/servers/{}/networks/'
                                    .format(node.id),
                                    method='POST')
        return result.status == 204

    def ex_link_ip_to_node(self, node, ip):
        """
        links a existing ip with a node

        :param node: node object
        :type node: ``object``

        :param ip: ip object
        :type ip: ``object``

        :return: Request ID
        :rtype: ``str``
        """
        result = self._sync_request(data=json.dumps({'object_uuid':
                                                    ip.id}),
                                    endpoint='objects/servers/{}/ips/'
                                    .format(node.id),
                                    method='POST')
        return result

    def ex_unlink_isoimage_from_node(self, node, isoimage):
        """
        unlink isoimages from server

        :param node: node you want to unlink the image from
        :type node: ``object``

        :param isoimage: isoimage you want to unlink
        :type isoimage: ``object``

        :return: None -> success
        :rtype: ``None``
        """
        result = self._sync_request(endpoint='objects/servers/{}/isoimages/{}'
                                    .format(node.id, isoimage.id),
                                    method='DELETE')
        return result

    def ex_unlink_ip_from_node(self, node, ip):
        """
        unlink ips from server

        :param node: node you want to unlink the ip from
        :type node: ``object``

        :param ip: the ip you want to unlink
        :type ip: ``object``

        :return: None -> success
        :rtype: ``None``
        """
        result = self._sync_request(endpoint='objects/servers/{}/ips/{}'
                                    .format(node.id, ip.id),
                                    method='DELETE')
        return result

    def ex_unlink_network_from_node(self, node, network):
        """
        Unlink network from node.

        :param node: Node you want to unlink from network.
        :type node: :class:`.Node`

        :param network: Network you want to unlink.
        :type network: :class:`.GridscaleNetwork

        :return: ``True`` if unlink was successful, otherwise ``False``
        :rtype: ``bool``
        """
        result = self._sync_request(endpoint='objects/servers/{}/networks/{}'
                                    .format(node.id, network.id),
                                    method='DELETE')
        return result.status == 204

    def detach_volume(self, volume):
        """
        Detaches a volume from a node.

        :param volume: Volume to be detached
        :type volume: :class:`.StorageVolume`

        :rtype: ``bool``
        """
        node = volume.extra['relations']['servers'][0]
        result = self._sync_request(endpoint='objects/servers/{}/storages/{}'
                                    .format(node['object_uuid'], volume.id),
                                    method='DELETE')
        return result.status == 204

    def ex_storage_rollback(self, volume, snapshot, rollback):
        """
        initiate a rollback on your storage

        :param volume: storage uuid
        :type volume: ``string``

        :param snapshot: snapshot uuid
        :type snapshot: ``string``

        :param rollback: variable
        :type rollback: ``bool``

        :return: RequestID
        :rtype: ``str``
        """
        result = self._sync_request(data=json.dumps({'rollback': rollback}),
                                    endpoint='objects/storages/{}/snapshots/'
                                             '{}/rollback'
                                    .format(volume.id, snapshot.id),
                                    method='PATCH')
        return result

    def _to_node(self, data):
        extra_keys = ['cores', 'power', 'memory', 'current_price', 'relations']

        extra = self._extract_values_to_dict(data=data, keys=extra_keys)
        ips = []

        for diction in data['relations']['public_ips']:
            ips.append(diction['ip'])

        state = ''

        if data['power'] is True:
            state = NodeState.RUNNING
        else:
            state = NodeState.STOPPED

        node = Node(id=data['object_uuid'], name=data['name'], state=state,
                    public_ips=ips,
                    created_at=parse_date(data['create_time']),
                    private_ips=None, driver=self.connection.driver,
                    extra=extra)

        return node

    def _to_volume(self, data):

        extra_keys = ['create_time', 'current_price', 'storage_type',
                      'relations']

        extra = self._extract_values_to_dict(data=data, keys=extra_keys)

        storage = StorageVolume(id=data['object_uuid'],
                                name=data['name'], size=data['capacity'],
                                driver=self.connection.driver,
                                extra=extra)

        return storage

    def _to_volume_snapshot(self, data):
        extra_keys = ['labels', 'status', 'usage_in_minutes',
                      'location_country', 'current_price', 'parent_uuid']

        extra = self._extract_values_to_dict(data=data, keys=extra_keys)

        volume_snapshot = VolumeSnapshot(id=data['object_uuid'],
                                         driver=self.connection.driver,
                                         size=data['capacity'], extra=extra,
                                         created=parse_date(
                                             data['create_time']),
                                         state=StorageVolumeState.AVAILABLE,
                                         name=data['name'])

        return volume_snapshot

    def _to_location(self, data):
        location = NodeLocation(id=data['object_uuid'], name=data['name'],
                                country=data['country'],
                                driver=self.connection.driver, )
        return location

    def _to_ip(self, data):
        ip = GridscaleIp(id=data['object_uuid'], family=data['family'],
                         prefix=data['prefix'],
                         create_time=data['create_time'],
                         address=data['ip'])

        return ip

    def _to_network(self, data):
        network = GridscaleNetwork(id=data['object_uuid'], name=data['name'],
                                   create_time=data['create_time'],
                                   status=data['status'],
                                   relations=data['relations'])
        return network

    def _to_node_image(self, data):
        extra_keys = ['capacity', 'create_time', 'labels', 'ostype',
                      'location_name', 'private', 'status',
                      'usage_in_minutes', 'version']

        extra = self._extract_values_to_dict(data=data, keys=extra_keys)

        template = NodeImage(id=data['object_uuid'], name=data['name'],
                             driver=self.connection.driver,
                             extra=extra)

        return template

    def _to_key(self, data):
        key = KeyPair(name=data['name'], fingerprint=data['object_uuid'],
                      public_key=data['sshkey'], private_key=None, extra=None,
                      driver=self.connection.driver)

        return key

    def _extract_values_to_dict(self, data, keys):
        """
        Extract extra values to dict.

        :param data: dict to extract values from.
        :type data: ``dict``
        :param keys: keys to extract
        :type keys: ``List``
        :return: dictionary containing extra values
        :rtype: ``dict``
        """

        result = {}

        for key in keys:
            if key == 'memory':
                result[key] = data[key] * 1024
            else:
                result[key] = data[key]

        return result

    def _get_response_dict(self, raw_response):
        """

        Get the actual response dictionary.

        :param raw_response: Nested dictionary.
        :type raw_response: ``dict``

        :return: Not-nested dictionary.
        :rtype: ``dict``
        """
        return list(raw_response.object.values())[0]

    def _get_resource(self, endpoint_suffix, object_uuid):
        """
        Get specific uuid specific resource.

        :param endpoint_suffix: Endpoint resource e.g. servers/.
        :type endpoint_suffix: ``str``
        :param object_uuid: Uuid of resource to be pulled.
        :type object_uuid: ``str``
        :return: Response dictionary.
        :rtype: nested ``dict``
        """
        data = self._sync_request(
            endpoint='objects/{}/{}'.format(endpoint_suffix, object_uuid))

        data = self._get_response_dict(data)

        return data
