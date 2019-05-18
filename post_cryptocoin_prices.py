#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post latest cryptocoin prices to slack."""
import sys
import os
import logging
import logging.config
import logging.handlers
import json
import urllib.request
import urllib.parse
import urllib.error
from configparser import ConfigParser
from argparse import ArgumentParser

import log_config


__version__ = '0.3.1'


def _parse_opts():
    """Parse the command line options.

    :param list argv: List of arguments to process. If not provided then will
        use optparse default
    :return: options,args where options is the list of specified options that
        were parsed and args is whatever arguments are left after parsing all
        options.
    """
    parser = ArgumentParser()
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    parser.add_argument(
        '--config', '-c', metavar='FILE',
        help='use config FILE (default: %(default)s)', default='config.ini')
    parser.add_argument(
        '--verbose', '-v', action='count',
        help='be more verbose. use -vv for more detail')
    parser.add_argument(
        '--dryrun', '-d', dest='dryrun', action='store_true',
        help='do not post to slack (default is to post to slack)')
    args = parser.parse_args()
    return args


def _get_coincap_usd(coin='BTC'):
    log = logging.getLogger('root._get_coincap_usd')
    req = urllib.request.Request(
        'https://coincap.io/page/{}'.format(coin))
    req.add_header(
        'User-Agent',
        'coincap2slack/{} (github.com/vrillusions/cryptocoin2slack)'.format(__version__))
    try:
        with urllib.request.urlopen(req) as f:
            data = json.loads(f.read().decode('utf-8'))
    except urllib.error.URLError as exc:
        log.error("could not retrieve value for {}: {}".format(
            coin, exc.reason))
        return 'err'
    log.debug(data)
    return '{:1.2f}'.format(round(data['price'], 2))


def _get_coinbase_spot(coin='BTC'):
    log = logging.getLogger('root._get_coinbase_spot')
    req = urllib.request.Request(
        'https://www.coinbase.com/api/v2/prices/{}-USD/spot'.format(coin))
    req.add_header('CB-VERSION', '2017-08-01')
    req.add_header(
        'User-Agent',
        'coincap2slack/{} (github.com/vrillusions/cryptocoin2slack)'.format(__version__))
    try:
        with urllib.request.urlopen(req) as f:
            spot_data = json.loads(f.read().decode('utf-8'))
    except urllib.error.URLError as exc:
        log.error("could not retrieve value for {}: {}".format(
            coin, exc.reason))
        return 'err'
    log.debug(spot_data)
    return '{:1.2f}'.format(round(float(spot_data['data']['amount']), 2))


def _post_slack_message(webhook_url, msg=None, channel=None):
    """Post message to a slack channel

    :param string webhook_url: required webhook url to use
    :param string msg: Message to post
    :param string channel: Optional channel to post to (by default will use webhook's) Should be full channel '#example' or '@username'
    """
    log = logging.getLogger('root._post_slack_message')
    payload = {}
    payload['text'] = msg
    if channel:
        payload['channel'] = channel
        log.debug('using non default channel {}'.format(channel))
    else:
        log.debug('using default channel specified in webhook')
    data = urllib.parse.urlencode({'payload': json.dumps(payload)})
    data = data.encode('ascii')
    with urllib.request.urlopen(webhook_url, data) as f:
        result = f.read().decode('utf-8')
    log.debug(result)


def main():
    """The main function.

    :param list argv: List of arguments passed to command line. Default is None,
        which then will translate to having it set to sys.argv.

    :return: Optionally returns a numeric exit code. If not given then will
        default to 0.
    :rtype: int
    """
    log = logging.getLogger('root')
    options = _parse_opts()
    if options.verbose:
        if options.verbose == 1:
            loglevel = 'INFO'
        elif options.verbose >= 2:
            loglevel = 'DEBUG'
        logging.config.dictConfig({
            "version": 1,
            "incremental": True,
            "handlers": {
                "console": { "level": loglevel },
                "file": { "level": loglevel },
            },
        })
    config = ConfigParser()
    config.read(options.config)
    slack_webhook_url = config['slack']['webhook_url']
    coin_prices = []
    if config['coins']['coinbase']:
        for coin in config['coins']['coinbase'].split(','):
            coin_prices.append('{}: {}'.format(coin, _get_coinbase_spot(coin)))
    if config['coins']['coincap'] != "":
        for coin in config['coins']['coincap'].split(','):
            coin_prices.append('{}: {}'.format(coin, _get_coincap_usd(coin)))
    msg = ' - '.join(coin_prices)
    log.info(msg)
    if not options.dryrun:
        if config['slack']['channels'] != "":
            for channel in config['slack']['channels'].split(','):
                if channel == 'DEFAULT':
                   _post_slack_message(slack_webhook_url, msg=msg)
                else:
                   _post_slack_message(
                        slack_webhook_url, msg=msg, channel=channel)


if __name__ == "__main__":
    # Configure logging only if called directly
    logging.config.dictConfig(log_config.config)
    sys.exit(main())
