#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post latest prices to slack.

Environment Variables
    LOGLEVEL: overrides the level specified here. Default is info
        option: DEBUG, INFO, WARNING, ERROR, or CRITICAL
"""
import sys
import os
import logging
import json
import urllib.request
import urllib.parse
from configparser import ConfigParser
from optparse import OptionParser


__version__ = '0.1.0'


def _parse_opts(argv=None):
    """Parse the command line options.

    :param list argv: List of arguments to process. If not provided then will
        use optparse default
    :return: options,args where options is the list of specified options that
        were parsed and args is whatever arguments are left after parsing all
        options.
    """
    parser = OptionParser(version='%prog {}'.format(__version__))
    parser.set_defaults(verbose=False, dryrun=False)
    parser.add_option(
        '-c', '--config', dest='config', metavar='FILE',
        help='use config FILE (default: %default)', default='config.ini')
    parser.add_option(
        '-v', '--verbose', dest='verbose', action='store_true',
        help='be more verbose (default is no)')
    parser.add_option(
        '-d', '--dryrun', dest='dryrun', action='store_true',
        help='do not post to slack (default is to post to slack)')
    (options, args) = parser.parse_args(argv)
    return options, args


def _get_coincap_usd(coin='BTC'):
    log = logging.getLogger('root._get_coincap_usd')
    req = urllib.request.Request(
        'https://coincap.io/page/{}'.format(coin))
    req.add_header(
        'User-Agent',
        'coincap2slack/{} (github.com/vrillusions/cryptocoin2slack)'.format(__version__))
    with urllib.request.urlopen(req) as f:
        data = json.loads(f.read().decode('utf-8'))
    log.debug(data)
    return '{:1.2f}'.format(data['price_usd'])


def _get_coinbase_spot(coin='BTC'):
    log = logging.getLogger('root._get_coinbase_spot')
    req = urllib.request.Request(
        'https://www.coinbase.com/api/v2/prices/{}-USD/spot'.format(coin))
    req.add_header('CB-VERSION', '2017-08-01')
    req.add_header(
        'User-Agent',
        'coincap2slack/{} (github.com/vrillusions/cryptocoin2slack)'.format(__version__))
    with urllib.request.urlopen(req) as f:
        spot_data = json.loads(f.read().decode('utf-8'))
    log.debug(spot_data)
    return spot_data['data']['amount']


def _post_slack_message(webhook_url, msg=None):
    log = logging.getLogger('root._post_slack_message')
    payload = {}
    payload['text'] = msg
    data = urllib.parse.urlencode({'payload': json.dumps(payload)})
    data = data.encode('ascii')
    with urllib.request.urlopen(webhook_url, data) as f:
        result = f.read().decode('utf-8')
    log.debug(result)


def main(argv=None):
    """The main function.

    :param list argv: List of arguments passed to command line. Default is None,
        which then will translate to having it set to sys.argv.

    :return: Optionally returns a numeric exit code. If not given then will
        default to 0.
    :rtype: int
    """
    log = logging.getLogger('root')
    if argv is None:
        argv = sys.argv
    options = _parse_opts(argv)[0]
    if options.verbose:
        log.setLevel(logging.DEBUG)
    config = ConfigParser()
    config.read('config.ini')
    slack_webhook_url = config['slack']['webhook_url']
    coin_prices = []
    for coin in config['coins']['coinbase'].split(','):
        coin_prices.append('{}: {}'.format(coin, _get_coinbase_spot(coin)))
    for coin in config['coins']['coincap'].split(','):
        coin_prices.append('{}: {}'.format(coin, _get_coincap_usd(coin)))
    msg = ' - '.join(coin_prices)
    log.info(msg)
    if not options.dryrun:
        _post_slack_message(slack_webhook_url, msg)


if __name__ == "__main__":
    # Configure logging only if called directly
    _loglevel = getattr(logging, os.getenv('LOGLEVEL', 'INFO').upper())
    _logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=_loglevel, format=_logformat)
    sys.exit(main())
