import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ur_operator')))

import pytest 

import ur_operator.handlers as handlers

def test_monitor_type_changed_changed_type():
    assert handlers.type_changed([['change', ['spec', 'type']]])


def test_monitor_type_changed_changed_name():
    assert not handlers.type_changed(
        [['change', ['spec', 'friendlyName']]])


def test_monitor_type_changed_added():
    assert not handlers.type_changed(
        [['add', ['spec', 'friendlyName']]])


def test_get_identifier_on_update():
    identifier = '123456'
    status = {
        handlers.on_update.__name__: {handlers.MONITOR_ID_KEY: identifier},
        handlers.on_create.__name__: {handlers.MONITOR_ID_KEY: '654321'}
    }

    assert handlers.get_identifier(status) == identifier

def test_get_identifier_on_create():
    identifier = '123456'
    status = {
        handlers.on_create.__name__: {handlers.MONITOR_ID_KEY: identifier}
    }

    assert handlers.get_identifier(status) == identifier

def test_get_identifier_missing():
    status = {}

    with pytest.raises(KeyError):
        handlers.get_identifier(status)