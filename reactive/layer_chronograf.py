# !/usr/bin/python3

import subprocess

from charmhelpers.core import unitdata
from charms.reactive import when, when_not, set_state, remove_state
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charmhelpers.core.hookenv import open_port, close_port, status_set
from charmhelpers.core.host import service_stop, service_restart
from charmhelpers.core.templating import render


DB = unitdata.kv()


@when_not('layer-chronograf.installed')
def install_layer_chronograf():
    """Installs the Chronograf software."""
    status_set('maintenance', 'Installing Chronograf...')
    fetcher = ArchiveUrlFetchHandler()
    fetcher.download('https://dl.influxdata.com/chronograf/releases/chronograf_1.3.3.0_amd64.deb',
                     '/opt/chronograf_1.3.3.0_amd64.deb')
    subprocess.check_call(['dpkg', '-i', '/opt/chronograf_1.3.3.0_amd64.deb'])
    set_state('layer-chronograf.installed')


@when('layer-chronograf.installed')
@when_not('layer-chronograf.influxdb-configured')
def set_blocked():
    status_set('blocked', 'Please create a relation with InfluxDB.')


@when('influxdb.available')
@when_not('layer-chronograf.influxdb-configured')
def configure_influxdb(influxdb):
    """Restarts Chronograf with information about InfluxDB instance."""
    DB.set('influxdb_hostname', influxdb.hostname())
    DB.set('influxdb_port', influxdb.port())
    DB.set('influxdb_user', influxdb.user())
    DB.set('influxdb_password', influxdb.password())

    context = {'options': get_options()}
    render('chronograf.service', '/lib/systemd/system/chronograf.service', context)
    render('chronograf.service', '/usr/lib/chronograf/scripts/chronograf.service', context)
    render('init.sh', '/usr/lib/chronograf/scripts/init.sh', context)

    subprocess.check_call(['sudo', 'systemctl', 'daemon-reload'])

    remove_state('layer-chronograf.started')
    set_state('layer-chronograf.influxdb-configured')


@when('layer-chronograf.installed')
@when('layer-chronograf.influxdb-configured')
@when_not('layer-chronograf.started')
def start_layer_chronograf():
    """Starts the Chronograf service."""
    status_set('maintenance', 'Starting up...')
    service_restart('chronograf')
    open_port(8888)
    set_state('layer-chronograf.started')
    status_set('active', 'Chronograf is running.')


@when('layer-chronograf.influxdb-configured')
@when_not('influxdb.available')
def wait_influx_available():
    # No relation so set InfluxDB values to None.
    DB.set('influxdb_hostname', None)
    DB.set('influxdb_port', None)
    DB.set('influxdb_user', None)
    DB.set('influxdb_password', None)
    service_stop('chronograf')
    close_port(8888)
    remove_state('layer-chronograf.influxdb-configured')


def get_options():
    """Returns string with options to run Chronograf with."""
    options = ""

    # If influxdb_hostname is None then that means there is no relation
    # with InfluxDB.
    if DB.get('influxdb_hostname') is not None:
        influxdb_url = 'http://' + DB.get('influxdb_hostname') + ':' + DB.get('influxdb_port')
        options = '--influxdb-url {} --influxdb-username {} --influxdb-password {}'.format(influxdb_url, DB.get('influxdb_user'), DB.get('influxdb_password'))

    return options
