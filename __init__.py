"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)

import chatgpt_flask_app.views
