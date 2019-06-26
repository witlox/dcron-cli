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
import os
import random

import requests
import click
import click_log

from dateutil import parser, tz

from cli.configuration import Configuration

logger = logging.getLogger()
click_log.basic_config(logger)


@click.group()
@click.option('-c', '--config-file', default='~/.dcron/sites.json', help='configuration file (created if not exists, default: ~/.dcron/sites.json)')
@click.option('-s', '--site-name', default='default', help='Name of the site to interact with (default: `default`)')
@click.option('-m', '--selection-mechanism', default='first', help='selection mechanism for communicating with our clusters (first, last, random, `ip`, default: first)')
@click.pass_context
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
        ctx.obj['PREFIX'] = 'https'
        ctx.obj['URI'] = "https://{0}:{1}".format(ctx.obj['ENTRY'], ctx.obj['SITE'].port)
    else:
        ctx.obj['PREFIX'] = 'http'
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
        logging.info('------------------------------------------------------')
        logging.info("{0} nodes in cluster".format(len(r.json())))
        for line in r.json():
            if 'ip' not in line:
                logger.error("could not find ip in state line: {0}".format(line))
            else:
                try:
                    if ctx.obj['SITE'].username:
                        r = requests.get("{0}://{1}:{2}/cron_in_sync".format(ctx.obj['PREFIX'], line['ip'], ctx.obj['SITE'].port), auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
                    else:
                        r = requests.get("{0}://{1}:{2}/cron_in_sync".format(ctx.obj['PREFIX'], line['ip'], ctx.obj['SITE'].port))
                    logging.info('******************************************************')
                    logging.info("ip           : {0}".format(line['ip']))
                    load = float(line['load'])
                    logging.info("load         : {0:.2f}%".format(load))
                    logging.info("state        : {0}".format(line['state']))
                    dt = parser.parse(line['time'])
                    logging.info("communicated : {0:%Y-%m-%d %H:%M}".format(dt.astimezone(tz.tzlocal())))
                    if r.status_code == 200:
                        logging.info('cron         : in sync')
                    else:
                        logging.info('cron         : out of sync')
                        logging.warning(r.text)
                except requests.exceptions.RequestException as re:
                    logger.error(re)
        logging.info('------------------------------------------------------')
    except requests.exceptions.RequestException as e:
        logger.error(e)


@cli.command(help='show cluster jobs')
@click.pass_context
def jobs(ctx):
    """
    report cluster jobs
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


@cli.command(help='show running cluster jobs')
@click.pass_context
def running(ctx):
    """
    report running cluster jobs
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
        running = []
        for line in r.json():
            if 'pid' in line and line['pid']:
                running.append(line)
        if len(running) == 0:
            logger.info("currently no running jobs on the cluster")
        else:
            for line in running:
                logger.info("job [{0}]: {1} {2}, running with pid {3}".format(line['assigned_to'], line['parts'], line['command'], line['pid']))
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
                logger.info("- running pid     : {0}".format(item['pid']))
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


@cli.command(help='export jobs on cluster')
@click.option('-f', '--file-name', help='export current jobs to file')
@click.option('--force', is_flag=True, help='overwrite if the file exists')
@click.pass_context
def export(ctx, file_name, force):
    """
    export jobs
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if ctx.obj['SITE'].username:
        r = requests.get("{0}/export".format(ctx.obj['URI']), auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
    else:
        r = requests.get("{0}/export".format(ctx.obj['URI']))
    if len(r.json()) == 0:
        logger.warning("no jobs found for exporting")
    else:
        logger.debug("got export data: {0}".format(r.json()))
        directory = os.path.dirname(file_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if os.path.exists(file_name):
            if force:
                os.remove(file_name)
                with open(file_name, 'wb') as fp:
                    fp.write(r.content)
                logger.info("successfully writen export to {0}".format(file_name))
            else:
                logger.error("file already exists (use --force to overwrite")
                exit(-33)
        else:
            with open(file_name, 'wb') as fp:
                fp.write(r.content)
            logger.info("successfully writen export to {0}".format(file_name))


@cli.command(name='import', help='import jobs on cluster')
@click.option('-f', '--file-name', help='import jobs from file to cluster')
@click.pass_context
def import_data(ctx, file_name):
    """
    export jobs
    """
    if not ctx.obj['SITE']:
        print('could not locate configuration object')
        exit(-10)

    if not os.path.exists(file_name):
        print("could not locate file for importing {0}".format(file_name))
        exit(-34)

    with open(file_name, 'rb') as fp:
        data = json.load(fp)

    try:
        if ctx.obj['SITE'].username:
            r = requests.post("{0}/import".format(ctx.obj['URI']), data={'payload': json.dumps(data)}, auth=(ctx.obj['SITE'].username, ctx.obj['SITE'].password))
        else:
            r = requests.post("{0}/import".format(ctx.obj['URI']), data={'payload': json.dumps(data)})
        if r.status_code == 200:
            logger.info("successfully imported data")
        else:
            logger.warning("unsuccessful request: {0} ({1})".format(r.text, r.status_code))
    except requests.exceptions.RequestException as e:
        logger.error(e)


def main():
    cli()


if __name__ == '__main__':
    cli()
