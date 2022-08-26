#
# Copyright 2021 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Original parts are Copyright 2016 OSGeo Foundation,            
# represented by PyWPS Project Steering Committee,               
# and released under MIT license.                                
# Please consult PYWPS_LICENCE.txt for details
#

from ..ogc import OGCTYPE_SCHEMA
from ..traits import register_trait

from pyqgiswps.validator.base import to_json_serializable

from typing import TypeVar

Json = TypeVar('Json')


class BasicOutputDescription:

    def ogcapi_description(self) -> Json:
        doc = {
            'title': self.title,
            'keywords': [],
            'metadata': [ m.ogcapi_metadata() for m in self.metadata ],
        }

        if self.abstract:
            doc.update(description=self.abstract)

        return doc



@register_trait
class LiteralOutput(BasicOutputDescription):
    
    def ogcapi_output_description(self) -> Json:
        """ Ogc api output description
        """
        doc = self.ogcapi_description()

        schema = OGCTYPE_SCHEMA[self.data_type]
        if self.uoms:
            schema.update(uom={
                'oneOf': [uom.ogcapi_description() for uom in self.uoms],
            })
        doc.update(schema=schema)
        return doc

    def ogcapi_output_result(self) -> Json:
        """ Return Json formated result 
        """
        data = to_json_serializable(self.data)
        if self.uom: 
            return {
                'value': data,
                'uom': self.uom.ogcapi_description(),
            }
        else:
            return data
    

@register_trait
class BoundingBoxOutput(BasicOutputDescription):

    def ogcapi_output_description(self) -> Json:

        doc = self.ogcapi_description()

        num_items = self.dimensions * 2
        
        schema = {
            'type': 'object',
            'required': ['bbox'],
            'format': 'ogc-bbox',
            'dimensions': self.dimensions,
            'properties': {
                'bbox': {
                    'type': 'array',
                    'minItems': num_items, 
                    'maxItems': num_items,
                    'items': { 'type': 'number' },
                },
                'crs': {
                    'type': 'string',
                    'default': self.crss[0],
                    'enum': [crs for crs in self.crss],
                },
            },
        }
       
        doc.update(schema=schema)
        return doc

    def ogcapi_output_result(self):
        """ OGC api json result 
        """
        bbox = self.data
        doc = {
            'crs': self.crs,
            'dimensions': self.dimensions,
            'bbox': [
                bbox[0],
                bbox[1],
                bbox[2],
                bbox[3],
            ],
        } 
        if self.dimensions >= 3: 
            doc.bbox.extend((bbox[4], bbox[5]))
        return doc


@register_trait
class ComplexOutput(BasicOutputDescription):
    
    def ogcapi_output_description(self) -> Json:

        doc = self.ogcapi_description()
        if self.supported_formats:
            if len(self.supported_formats) > 1:
                def schemas():
                    for fmt in self.supported_formats:
                        schema = fmt.ogcapi_description()
                        schema['type'] = 'string'
                        yield schema
                schema={'oneOf': list(schemas())}
            else:
                schema = self.supported_formats[0].ogcapi_description()
                schema['type'] = 'string'
        else:
            schema = { 'type': 'string' }
        doc.update(schema=schema)
        return doc

    def ogcapi_output_result(self) -> Json:
        """ OGC api json result
        """
        if self.as_reference:
            if self.url is None:
                raise ValueError("Missing url")
            doc = {
                'href': self.url,
                'type': self.data_format.mime_type,
            }
        else:
            data = self.data
            encoding = self.data_format.encoding
            schema = self.data_format.schema
            if data is not None:
                if not isinstance(data, str):
                    data = self.base64
                    encoding = 'base64'
            doc = { 'value': data, 'mediaType': self.data_format.mime_type }
            if encoding:
                doc.update(encoding=encoding)
            if self.schema:
                doc.update(schema=schema)
        return doc

