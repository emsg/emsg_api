#/usr/bin/env python
#coding=utf8
import traceback
from django.http import HttpResponse

from django.shortcuts import render
import json
import logging
import errors
from service import *
from service_emsg import *
import emsg_simple_api.utils as utils
logger = logging.getLogger(__name__)

def main(request):
    if request.method == 'GET':
        logger.debug('get')
        body = request.GET.get('body')
    elif request.method == 'POST':
        logger.debug('post')
        logger.debug(request.POST)
        body = request.POST.get('body')
    logger.info('[INPUT] %s' % body)
    sn = ''
    try:
        param = json.loads(body)
        sn = param.get('sn')
        service = param['service']
        method = param['method']
        s = eval('%s()' % service)
        m = getattr(s,method)
        success = m(param)
        response_success = utils.json_encode(success)
        logger.info('[OUTPUT] %s' % response_success)
        return HttpResponse(response_success,charset='utf8',content_type='text/json')
    except :
        logger.error(traceback.format_exc())
        return HttpResponse(json.dumps(dict(
            sn=sn,success=False,entity=dict(
                code='1000',
                reason=errors.error_1000
            )
        )),
        charset='utf8',content_type='text/json')



