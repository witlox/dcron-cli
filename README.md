## Distributed Cronlike Scheduler [![Build Status](https://travis-ci.org/witlox/dcron.svg?branch=master)](https://travis-ci.org/witlox/dcron)

The aim of dcron is to offer [cron](https://en.wikipedia.org/wiki/Cron) like behaviour spanning multiple machines. 
The system offers a web interface to manage your jobs, and reports the health of the cluster. 
Everything is self contained, so you only need to start the system to have a working setup. 
We do however recommend that you run the system behind a reverse proxy, since there is no authentication mechanism.
Please check the [docs](https://dcron.readthedocs.io) regarding installation, configuration and options.  

## Details

- dcron requires Python 3.7+ in order to work.
- all nodes running dcron need to have the same software installed you want dcron to run
- dcron runs tasks at-most-once (according to schedule)

## Installation

``pip install dcron``
