#!/usr/bin/env python
# -*- coding: utf-8 -*-#

# MIT License
#
# Copyright (c) 2019 Pim Witlox
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import logging
import random

import requests
import click
import click_log

from cli.configuration import Configuration

logger = logging.getLogger()
click_log.basic_config(logger)


@click.group()
@click.option('-c', '--config-file', default='~/.dcron/sites.json', help='configuration file (created if not exists, default: ~/.dcron/sites.json)')
@click.option('-s', '--site-name', default='default', help='Name of the site to interact with (default: `default`)')
@click.option('-m', '--selection-mechanism', default='first', help='selection mechanism for communicating with our clusters (first, last, random, `ip`, default: first)')
@click.pass_context
@click_log.simple_verbosity_option(logger)
def cli(ctx, config_file, site_name, selection_mechanism):
    """
    This CLI allows you to manage dcron installations. Check your config file for settings, the
    default location is in your home folder under `~/.dcron/sites.json`.
    """
    ctx.obj = {}

    config_file = Configuration(config_file)
    ctx.obj['SITE'] = next(iter([s for s in config_file.sites if s.name == site_name]), None)

    if not ctx.obj['SITE']:
        print("site {0} not found in configuration! aborting...".format(site_name))
        exit(-1)
    if len(ctx.obj['SITE'].servers) == 0:
        print("site {0} has no servers configured! aborting...".format(site_name))
        exit(-2)

    if selection_mechanism == 'first':
        ctx.obj['ENTRY'] = sorted(ctx.obj['SITE'].servers)[0]
    elif selection_mechanism == 'last':
        ctx.obj['ENTRY'] = sorted(ctx.obj['SITE'].servers, reverse=True)[0]
    elif selection_mechanism == 'random':
        ctx.obj['ENTRY'] = random.choice(ctx.obj['SITE'].servers)
    else:
        specific = next(iter([s for s in ctx.obj['SITE'].servers if s == selection_mechanism]), None)
        if not specific:
            print("could not find {0} for {1} in specified servers ({2})".format(selection_mechanism, site_name, ', '.join(ctx.obj['SITE'].servers)))
            exit(-3)
        ctx.obj['ENTRY'] = specific

    if ctx.obj['SITE'].ssl:
        ctx.obj['URI'] = "https://{0}:{1}".format(ctx.obj['ENTRY'], ctx.obj['SITE'].port)
    else:
        ctx.obj['URI'] = "http://{0}:{1}".format(ctx.obj['ENTRY'], ctx.obj['SITE'].port)

    if ctx.obj['SITE'].log_level == 'debug' or ctx.obj['SITE'].log_level == 'verbose':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


@cli.command(help='show cluster status')
@click.pass_context
def status(ctx):
    """
    report cluster status
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    try:
        if ctx.obj['SITE'].username:
            r = requests.get("{0}/status".format(ctx.obj['URI']), auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.get("{0}/status".format(ctx.obj['URI']))
        if len(r.json()) == 0:
            logger.error("could not retrieve cluster state!")
        for line in r.json():
            del(line['_type'])
            logger.info(line)
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='show cluster jobs')
@click.pass_context
def jobs(ctx):
    """
    report cluster status
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    try:
        if ctx.obj['SITE'].username:
            r = requests.get("{0}/jobs".format(ctx.obj['URI']), auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.get("{0}/jobs".format(ctx.obj['URI']))
        if len(r.json()) == 0:
            logger.info("currently no jobs on the cluster")
        for line in r.json():
            logger.info("job [{0}]: {1} {2}".format(line['assigned_to'], line['parts'], line['command']))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='add job to cluster')
@click.option('-p', '--pattern', default="* * * * *", help='cron pattern to use')
@click.option('-c', '--command', help='command to execute from cron')
@click.option('--enabled', is_flag=True, help='enable the job on submission')
@click.pass_context
def add(ctx, pattern, command, enabled):
    """
    add a cron job to the cluster
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not len(pattern.split(' ')) == 5:
        print('pattern not valid, should follow cron pattern (* * * * *)')
        exit(-11)

    data = {
        'command': command,
        'minute': pattern.split(' ')[0],
        'hour': pattern.split(' ')[1],
        'dom': pattern.split(' ')[2],
        'month': pattern.split(' ')[3],
        'dow': pattern.split(' ')[4],
    }

    if not enabled:
        data['disabled'] = 'true'

    try:
        if ctx.obj['SITE'].username:
            r = requests.post("{0}/add_job".format(ctx.obj['URI']), data=data, auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.post("{0}/add_job".format(ctx.obj['URI']), data=data)
        if r.status_code == 201:
            logger.info("successfully submitted job {0} with pattern {1} (enabled: {2})".format(command, pattern, enabled))
        else:
            logger.warning("unsuccessful request: {0} ({1})".format(r.text, r.status_code))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='remove job from cluster')
@click.option('-p', '--pattern', help='cron pattern to use')
@click.option('-c', '--command', help='command to execute from cron')
@click.pass_context
def remove(ctx, pattern, command):
    """
    remove a cron job from the cluster
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not len(pattern.split(' ')) == 5:
        print('pattern not valid, should follow cron pattern (* * * * *)')
        exit(-11)

    data = {
        'command': command,
        'minute': pattern.split(' ')[0],
        'hour': pattern.split(' ')[1],
        'dom': pattern.split(' ')[2],
        'month': pattern.split(' ')[3],
        'dow': pattern.split(' ')[4],
    }

    try:
        if ctx.obj['SITE'].username:
            r = requests.post("{0}/remove_job".format(ctx.obj['URI']), data=data, auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.post("{0}/remove_job".format(ctx.obj['URI']), data=data)
        if r.status_code == 200:
            logger.info("successfully submitted remove request {0} with pattern {1}".format(command, pattern))
        else:
            logger.warning("unsuccessful request: {0} ({1})".format(r.text, r.status_code))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='job details from cluster')
@click.option('-p', '--pattern', help='cron pattern to use')
@click.option('-c', '--command', help='command to execute from cron')
@click.pass_context
def details(ctx, pattern, command):
    """
    get job details
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not len(pattern.split(' ')) == 5:
        print('pattern not valid, should follow cron pattern (* * * * *)')
        exit(-11)

    try:
        if ctx.obj['SITE'].username:
            r = requests.get("{0}/jobs".format(ctx.obj['URI']), auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.get("{0}/jobs".format(ctx.obj['URI']))

        if len(r.json()) == 0:
            logger.info("currently no jobs on the cluster")
        else:
            item = None
            for line in r.json():
                if 'parts' in line and 'command' in line and line['parts'] == pattern and line['command'] == command:
                    item = line
            if item:
                logger.info("Job {0} {1} details:".format(pattern, command))
                logger.info("***********************************************")
                logger.info("- assigned to node: {0}".format(item['assigned_to']))
                logger.info("- last run        : {0}".format(item['last_run']))
                logger.info("- enabled         : {0}".format(item['enabled']))
                logger.info("- user            : {0}".format(item['user']))
                logger.info("- cron            : {0}".format(item['cron']))
                if 'log' in item and len(item['log']) > 0:
                    logger.info("-----------------------------------------------")
                    logger.info("last log: {0}".format(item['log'][0]))
                logger.info("***********************************************")
            else:
                logger.warning("could not find job matching {0} {1}".format(pattern, command))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='job logs from cluster')
@click.option('-p', '--pattern', help='cron pattern to use')
@click.option('-c', '--command', help='command to execute from cron')
@click.pass_context
def logs(ctx, pattern, command):
    """
    get job logs
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not len(pattern.split(' ')) == 5:
        print('pattern not valid, should follow cron pattern (* * * * *)')
        exit(-11)

    try:
        if ctx.obj['SITE'].username:
            r = requests.get("{0}/jobs".format(ctx.obj['URI']), auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.get("{0}/jobs".format(ctx.obj['URI']))

        if len(r.json()) == 0:
            logger.info("currently no jobs on the cluster")
        else:
            item = None
            for line in r.json():
                if 'parts' in line and 'command' in line and line['parts'] == pattern and line['command'] == command:
                    item = line
            if item and 'log' in item and len(item['log']) > 0:
                logger.info("Job {0} {1} logs:".format(pattern, command))
                logger.info("***********************************************")
                for line in item['log']:
                    logger.info(line)
                logger.info("***********************************************")
            else:
                logger.warning("No logs for job matching {0} {1}".format(pattern, command))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='run defined job on cluster')
@click.option('-p', '--pattern', help='cron pattern to use')
@click.option('-c', '--command', help='command to execute from cron')
@click.pass_context
def run(ctx, pattern, command):
    """
    run job
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not len(pattern.split(' ')) == 5:
        print('pattern not valid, should follow cron pattern (* * * * *)')
        exit(-11)

    data = {
        'command': command,
        'minute': pattern.split(' ')[0],
        'hour': pattern.split(' ')[1],
        'dom': pattern.split(' ')[2],
        'month': pattern.split(' ')[3],
        'dow': pattern.split(' ')[4],
    }

    try:
        if ctx.obj['SITE'].username:
            r = requests.post("{0}/run_job".format(ctx.obj['URI']), data=data, auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.post("{0}/run_job".format(ctx.obj['URI']), data=data)
        if r.status_code == 202:
            logger.info("successfully submitted run request {0} with pattern {1}".format(command, pattern))
        else:
            logger.warning("unsuccessful request: {0} ({1})".format(r.text, r.status_code))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='kill defined job on cluster')
@click.option('-p', '--pattern', help='cron pattern to use')
@click.option('-c', '--command', help='command to execute from cron')
@click.pass_context
def kill(ctx, pattern, command):
    """
    kill job
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not len(pattern.split(' ')) == 5:
        print('pattern not valid, should follow cron pattern (* * * * *)')
        exit(-11)

    data = {
        'command': command,
        'minute': pattern.split(' ')[0],
        'hour': pattern.split(' ')[1],
        'dom': pattern.split(' ')[2],
        'month': pattern.split(' ')[3],
        'dow': pattern.split(' ')[4],
    }

    try:
        if ctx.obj['SITE'].username:
            r = requests.post("{0}/kill_job".format(ctx.obj['URI']), data=data, auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.post("{0}/kill_job".format(ctx.obj['URI']), data=data)
        if r.status_code == 202:
            logger.info("successfully submitted run request {0} with pattern {1}".format(command, pattern))
        else:
            logger.warning("unsuccessful request: {0} ({1})".format(r.text, r.status_code))
    except requests.exceptions.RequestException as e:
        logger.error(e)


def main():
    cli()


if __name__ == '__main__':
    cli()