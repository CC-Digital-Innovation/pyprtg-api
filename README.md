# PyPRTG API

Python client module to communicate with PRTG instances. This module leverages PRTG's existing API and wraps it into an easy to understand Python class.

## Table of Contents

* [Getting Started](#getting-started)
    * [Requirements](#requirements)
    * [Installation](#installation)
    * [Usage](#usage)
* [TODOs](#todos)
* [Author](#author)
* [License](#license)

## Getting Started

### Requirements


* Python 3
    * _Tested with version 3.9.13. Some older versions will probably work but has not been extensively tested._

### Installation

```bash
pip install pyprtg-api
```

### Usage

```python
from prtg import ApiClient
from prtg.auth import BasicPasshash

auth = BasicPasshash('username', 'passhash')
client = ApiClient('https://prtg.instance.com', auth)

print(client.get_probe(1))
# {'objid': 1, 'objid_raw': 1, 'name': 'Probe Device', 'name_raw': 'Probe Device', 'active': True, 'active_raw': -1, 'tags': '', 'tags_raw': '', 'parentid': 0, 'parentid_raw': 0, 'priority': '3', 'priority_raw': 3, 'status': 'Up', 'status_raw': 3, 'groupnum': '7', 'groupnum_raw': 7, 'devicenum': '3', 'devicenum_raw': 3, 'location': '', 'location_raw': ''}
```

## TODOs
* Retrieve sensors
* Add sensors based on template

## Author
* Jonny Le <<jonny.le@computacenter.com>>

## License
MIT License

Copyright (c) 2021 Computacenter Digital Innovation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
