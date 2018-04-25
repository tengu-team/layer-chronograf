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
    """A relation with InfluxDB is required."""
    status_set('blocked', 'Please create a relation with InfluxDB.')


@when('influxdb.available')
@when_not('layer-chronograf.influxdb-configured')
def configure_influxdb(influxdb):
    """Relation with InfluxDB has been added. Restarts Chronograf with
    information about InfluxDB application."""
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


@when('kapacitor.available')
@when_not('layer-chronograf.kapacitor-configured')
def configure_kapacitor(kapacitor):
    """Relation with Kapacitor has been added. Restarts Chronograf with
    information about Kapacitor application."""
    DB.set('kapacitor_hostname', kapacitor.host())
    DB.set('kapacitor_port', kapacitor.port())
    DB.set('kapacitor_user', kapacitor.username())
    DB.set('kapacitor_password', kapacitor.password())

    context = {'options': get_options()}
    render('chronograf.service', '/lib/systemd/system/chronograf.service', context)
    render('chronograf.service', '/usr/lib/chronograf/scripts/chronograf.service', context)
    render('init.sh', '/usr/lib/chronograf/scripts/init.sh', context)

    subprocess.check_call(['sudo', 'systemctl', 'daemon-reload'])

    remove_state('layer-chronograf.started')
    set_state('layer-chronograf.kapacitor-configured')


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
def unconfigure_influxdb():
    """When relation with InfluxDB is removed Chronograf has to be stopped."""
    # No relation so set InfluxDB values to None.
    DB.set('influxdb_hostname', None)
    DB.set('influxdb_port', None)
    DB.set('influxdb_user', None)
    DB.set('influxdb_password', None)
    service_stop('chronograf')
    close_port(8888)
    remove_state('layer-chronograf.influxdb-configured')


@when('layer-chronograf.kapacitor-configured')
@when_not('kapacitor.available')
def unconfigure_kapacitor():
    # No relation so set Kapacitor values to None.
    DB.set('kapacitor_hostname', None)
    DB.set('kapacitor_port', None)
    DB.set('kapacitor_user', None)
    DB.set('kapacitor_password', None)
    remove_state('layer-chronograf.kapacitor-configured')


@when('layer-chronograf.started', 'http.available')
@when_not('http.configured')
def configure_http(http):
    http.configure(8888)


def get_options():
    """Returns string with options to run Chronograf with. (CLI arguments)"""
    options = ""
    # If influxdb_hostname is None then that means there is no relation
    # with InfluxDB.
    if DB.get('influxdb_hostname') is not None:
        influxdb_url = 'http://' + DB.get('influxdb_hostname') + ':' + DB.get('influxdb_port')
        option = '--influxdb-url {} --influxdb-username {} --influxdb-password {}'.format(influxdb_url, DB.get('influxdb_user'), DB.get('influxdb_password'))
        options = add_option(options, option)
    if DB.get('kapacitor_hostname') is not None:
        kapacitor_url = 'http://' + DB.get('kapacitor_hostname') + ':' + DB.get('kapacitor_port')
        option = '--kapacitor-url {} --kapacitor-username {} --kapacitor-password {}'.format(kapacitor_url, DB.get('kapacitor_user'), DB.get('kapacitor_password'))
        options = add_option(options, option)

    return options


def add_option(options, option):
    """Adds an option to a list of options."""
    if not options:
        options += option
    else:
        options += " "
        options += option
    return options
