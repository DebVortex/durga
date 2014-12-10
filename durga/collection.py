# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import itertools

import requests

from . import exceptions
from .element import Element


class Collection(object):
    def __init__(self, url, resource):
        self.url = url
        self.resource = resource
        self._reset_params()

    def all(self):
        self._reset_params()
        return self

    def filter(self, *args, **kwargs):
        self._reset_data()
        self.params.update(kwargs)
        return self

    def order_by(self):
        return self

    def count(self):
        return len(self)

    def get(self, *args, **kwargs):
        self.params.update(kwargs)
        count = self.count()
        if count > 1:
            raise exceptions.MultipleObjectsReturned
        elif count == 0:
            raise exceptions.ObjectNotFound
        return self._elements[0]

    def create(self, data):
        pass

    def update(self, data):
        pass

    def delete(self):
        pass

    def _reset_data(self):
        self.raw = self.data = self.validated_data = self._elements = None

    def _reset_params(self):
        self._reset_data()
        self.params = getattr(self.resource, 'query', {}).copy()

    def _query(self):
        if not self._elements:
            response = requests.get(self.url, params=self.params)
            self.raw = response.raw
            self.data = response.json()
            for key in self.resource.results_path:
                self.data = self.data[key]
            self.validated_data = self.validate(self.data)
            self._elements = [self.get_element(data) for data in self.validated_data]

    def validate(self, data):
        return [self.resource.schema.validate(item) for item in data]

    def get_element(self, data):
        if not getattr(self, 'element_class', False):
            prefix = self.resource.name.title().replace('/', '')
            self.element_class = str('{0}Element'.format(prefix))
        if not getattr(self, 'element_base', False):
            self.element_base = getattr(self.resource, 'Element', Element)
        return type(self.element_class, (self.element_base,), data)(self.resource, data)

    def get_element_url(self, id):
        self.resource.schema._schema[self.resource.get_id_attribute()].validate(id)
        return '{0}/{1}'.format(self.resource.get_url(), id)

    def __getitem__(self, key):
        """Returns a single Element or a slice of Elements."""
        self._query()
        if isinstance(key, slice):
            return itertools.islice(self._elements, *key.indices(self.count()))
        else:
            return self._elements[key]

    def __iter__(self):
        self._query()
        return iter(self._elements)

    def __len__(self):
        self._query()
        return len(self._elements)
