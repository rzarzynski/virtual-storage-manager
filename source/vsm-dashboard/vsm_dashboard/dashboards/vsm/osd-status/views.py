# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Corporation, All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import os
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListOSDStatusTable
from django.http import HttpResponse
from vsm_dashboard.common.horizon.summary import SummaryRenderer
import json
LOG = logging.getLogger(__name__)

from django.utils.datastructures import SortedDict

from vsm_dashboard.dashboards.vsm.overview.summarys import OsdSummary
from vsm_dashboard.utils import get_time_delta

class ModalSummaryMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        context['summary'] = OsdSummary(self.request)
        return context

class IndexView(ModalSummaryMixin, tables.DataTableView):
    table_class = ListOSDStatusTable
    template_name = 'vsm/osd-status/index.html'

    def get_data(self):
        default_limit = 10000;
        default_sort_dir = "asc";
        default_sort_keys = ['osd_name']
        marker = self.request.GET.get('marker', "")

        try:
            _osd_status = vsmapi.osd_status(self.request, paginate_opts={
                "limit": default_limit,
                "sort_dir": default_sort_dir,
                "marker":   marker,
            })

            if _osd_status:
                logging.debug("resp body in view: %s" % _osd_status)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve osd list. '))

        page_index = int(self.request.GET.get('pageIndex',1))
        page_size = 20
        page_count = int(len(_osd_status)/page_size)
        page_mod = len(_osd_status)%page_size
        if page_mod > 0:
            page_count = page_count + 1
        pager_size = 10
        pager_count = int(page_count/(pager_size))
        pager_index = int(page_index/(pager_size))
        if page_count%pager_size > 0:
            pager_count = pager_count + 1
        if page_index%pager_size > 0:
            pager_index = pager_index + 1

        dataStartIndex = (page_index-1)*page_size
        dataEndIndex = dataStartIndex+page_size
        _osd_status = _osd_status[dataStartIndex:dataEndIndex]


        osd_status = []
        for _osd in _osd_status:
            LOG.info("DEVICE:%s"%_osd.device.keys())
            #LOG.error(_osd.device.keys())
            #LOG.error(">DEVICE")
            osd = {
                "id":_osd.id,
                "osd_name": _osd.osd_name,
                "vsm_status": _osd.operation_status,
                "osd_state": _osd.state,
                "crush_weight": _osd.weight,
                "capacity_total": 0 if not _osd.device['total_capacity_kb']\
            else int(_osd.device['total_capacity_kb']/1024),#TODO dict to obj ?
                "capacity_used": 0 if not _osd.device['used_capacity_kb']\
            else int(_osd.device['used_capacity_kb']/1024),
                "capacity_avail": 0 if not _osd.device['avail_capacity_kb']\
            else int(_osd.device['avail_capacity_kb']/1024),
                "capacity_percent_used": 0 if not _osd.device['total_capacity_kb'] \
                    else _osd.device['used_capacity_kb']\
                    * 100 / _osd.device['total_capacity_kb'], #TODO
                "server": _osd.service['host'],
                "storage_group": _osd.storage_group['name'],
                "zone": _osd.zone,
                "updated_at": get_time_delta(_osd.updated_at),
                "pageCount":page_count,
                "pageIndex":page_index,
                "pagerCount":pager_count,
                "pagerIndex":pager_index,
                "deviceInfo":""
                }

            osd_status.append(osd)
        return osd_status
