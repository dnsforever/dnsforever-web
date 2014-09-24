DNS Forever web
===============

.. code-block:: console

    $ git clone https://github.com/dnsforever/dnsforever-web
    $ cd dnsforever-web/
    $ virtualenv venv
    $ . ./venv/bin/activate
    $ pip install -r requirements.txt 
    $ ./manage.py initdb 
    $ ./manage.py run -p 7890
