This is a plugin for `ofxstatement`_ to parse and convert proprietary bank statements of certain banks in Latvia to `OFX`_ files.

Statements from these banks are currently supported:

* `Swedbank`_ - CSV, FIDAVISTA xml files
* `DNB`_ - FIDAVISTA xml files
* `Citadele`_ - FIDAVISTA v1.2 xml files
* `SEB`_ - CSV files

.. _ofxstatement: https://github.com/kedder/ofxstatement
.. _OFX: http://en.wikipedia.org/wiki/Open_Financial_Exchange
.. _Swedbank: https://www.swedbank.lv/
.. _DNB: https://www.dnb.lv/
.. _Citadele: http://www.citadele.lv/
.. _SEB: http://www.seb.lv/


## Development
To run locally and edit the code, do the following:
```
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```
