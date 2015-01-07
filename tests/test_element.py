# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import httpretty
import pytest

from durga import element


def test_get_default_url_attribute(resource):
    class DefaultURLElement(element.Element):
        url = 'https://api.example.com/movies/23'

    assert DefaultURLElement(resource, {}).get_url() == DefaultURLElement.url


def test_get_custom_url_attribute(resource):
    resource.url_attribute = 'resource_uri'

    class CustomURLElement(element.Element):
        resource_uri = 'https://api.example.com/movies/23'

    assert CustomURLElement(resource, {}).get_url() == CustomURLElement.resource_uri


def test_get_dynamic_url(resource):
    class DynamicURLElement(element.Element):
        id = '23'

    with pytest.raises(AssertionError) as excinfo:
        DynamicURLElement(resource, {}).get_url()
    assert excinfo.value.msg == 'You must define an id_attribute attribute at MoviesResource.'
    resource.id_attribute = 'id'
    element_obj = DynamicURLElement(resource, {})
    assert element_obj.get_url() == '/'.join([resource.get_url(), element_obj.id])


@pytest.mark.httpretty
def test_update(fixture, resource):
    resource.url_attribute = 'resource_uri'
    body = fixture('movie.json')
    httpretty.register_uri(httpretty.GET, resource.get_url(), body=body,
        content_type='application/json')
    movie = resource.collection.get(id=1)

    def update_element(method, uri, headers):
        import json
        content = movie.get_raw()
        content.update(json.loads(method.body.decode('utf-8')))
        return (200, headers, json.dumps(content))

    httpretty.register_uri(httpretty.PUT, movie.get_url(), body=update_element,
        content_type='application/json')
    data = {'runtime': 90}
    assert movie.update(data).runtime == data['runtime']


@pytest.mark.httpretty
def test_delete(fixture, resource):
    resource.url_attribute = 'resource_uri'
    httpretty.register_uri(httpretty.GET, resource.get_url(), body=fixture('movie.json'),
        content_type='application/json')
    movie = resource.collection.get(id=1)
    httpretty.register_uri(httpretty.DELETE, movie.get_url(), status=204)
    response = movie.delete()
    assert response.status_code == 204
