# -*- coding: utf-8 -*-

import os
import re
import logging
import requests

from datetime import datetime

from flask import request
from flask import Flask


NEXMO_API_KEY = os.environ.get('NEXMO_API_KEY')
NEXMO_API_SECRET = os.environ.get('NEXMO_API_SECRET')

SET_CID_HEADER = re.compile('To: (\+?[0-9]{5,15})\n\n')


app = Flask(__name__)


@app.route('/nexmo/forward-sms/<forward_to>', methods=['POST'])
def nexmo_forward_sms(forward_to):
    received_at = request.form.get('message-timestamp')
    if received_at:
        received_at = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
    else:
        received_at = datetime.now()

    body = request.form.get('text')
    from_ = request.form.get('msisdn')
    to = request.form.get('to')
    message_id = request.form.get('messageId')

    if not message_id:
        return ''

    is_trusted_caller = forward_to == from_
    set_to = SET_CID_HEADER.match(body)

    if is_trusted_caller and set_to:
        forward_to = set_to.group(1)
        body = body.replace(set_to.group(0), '')
    else:
        body = u'[{0}]\n'.format(from_) + body

    _nexmo_send_sms(to=forward_to, body=body, from_=to)

    return ''


def _nexmo_send_sms(to, body, from_=None):
    if not NEXMO_API_KEY or not NEXMO_API_KEY:
        raise Exception("NEXMO API KEY is not set!")

    data = {
        'api_key': NEXMO_API_KEY,
        'api_secret': NEXMO_API_SECRET,
        'from': from_,
        'to': to,
        'text': body,
    }

    r = requests.post("https://rest.nexmo.com/sms/json", data)

    if r.status_code != 200:
        logging.error(r.text)
