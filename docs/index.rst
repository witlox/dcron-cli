.. dcron documentation master file, created by
   sphinx-quickstart on Thu Jan 24 13:44:01 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _dcron: https://github.com/witlox/dcron

Welcome to dcron-cli's documentation!
=====================================

The aim of dcron_ is to offer cron like behaviour spanning multiple machines.
This is a command line interface for interacting with dcron_.

Installing the package
======================
You need python 3.4+ or higher to run this package. The package can be installed using ``pip install dcron-cli``.

Running the package
===================
Our package is self contained, so you can start it by simply calling ``dcron-cli``.

Command line flags
==================

.. code-block:: console

Usage: dcron-cli [OPTIONS] COMMAND [ARGS]...

  This CLI allows you to manage dcron installations. Check your config file
  for settings, the default location is in your home folder under
  `~/.dcron/sites.json`.

Options:
  -c, --config-file TEXT          configuration file (created if not exists,
                                  default: ~/.dcron/sites.json)
  -s, --site-name TEXT            Name of the site to interact with (default:
                                  `default`)
  -m, --selection-mechanism TEXT  selection mechanism for communicating with
                                  our clusters (first, last, random, `ip`,
                                  default: first)
  --help                          Show this message and exit.

Commands:
  a        add a site
  add      add job to cluster
  details  job details from cluster
  export   export jobs on cluster
  import   import jobs on cluster
  info     get site info
  jobs     show cluster jobs
  kill     kill defined job on cluster
  logs     job logs from cluster
  ls       list all site names
  remove   remove job from cluster
  rm       remove an existing site
  run      run defined job on cluster
  running  show running cluster jobs
  status   show cluster status

sites.json
==========

Sites is a JSON serialized file which has the following form:

.. code-block:: console

   [{"_type": "site", "name": "default", "servers": "[\"localhost\"]", "port": 8080, "ssl": false, "log_level": "info", "username": "", "password": ""}]

In order to add a site, add a block between brackets and fill in the name and servers (optionally configure http basic authentication with username and password.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
