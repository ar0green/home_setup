#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.log import enable_pretty_logging
from application import app

enable_pretty_logging()

# PORT = 4000

# ------- DEVELOPMENT CONFIG -------
app.run(host='0.0.0.0', debug=False, threaded=True)
