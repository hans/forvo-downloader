import argparse
import configparser
import json
import os.path
import shutil
import unicodedata
import urllib.parse
import urllib.request
import sys

DEFAULT_CONFIG_LOCATION = '~/.forvo_downloader.cfg'
SEARCH_ENDPOINT = ('http://apifree.forvo.com/key/{api_key}/format/json/action'
                   '/pronounced-words-search/pagesize/100/search/{word}{extra}')

def parse_config(argv=None):
    if argv is None:
        argv = sys.argv

    conf_parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    conf_parser.add_argument('-c', '--conf-file', metavar='FILE',
                             help=('Specify config file location (default {})'
                                   .format(DEFAULT_CONFIG_LOCATION)),
                             default=DEFAULT_CONFIG_LOCATION)
    args, remaining_argv = conf_parser.parse_known_args()

    conf_path = os.path.expanduser(args.conf_file)
    if os.path.isfile(conf_path):
        config = configparser.ConfigParser()
        config.read([conf_path])
        defaults = dict(config.items("downloader"))
    else:
        defaults = {}

    # Parse rest of arguments
    parser = argparse.ArgumentParser(parents=[conf_parser])
    parser.set_defaults(**defaults)

    parser.add_argument('-k', '--api-key', metavar='KEY', help='Forvo API key')
    parser.add_argument('-l', '--language', metavar='LANGUAGE_CODE',
                        help=('Forvo language code (see '
                              'http://www.forvo.com/languages-codes/)'))
    parser.add_argument('word', metavar='WORD', help='Word to search on Forvo')
    args = parser.parse_args(remaining_argv)

    if 'api_key' not in args:
        raise ValueError('Must provide API key via `-k` option or in config '
                         'file')

    return vars(args)


def do_search(config):
    extra = ('/language/{}'.format(config['language'])
             if 'language' in config else '')
    word_fmt = urllib.parse.quote(config['word'])

    url = SEARCH_ENDPOINT.format(api_key=config['api_key'], word=word_fmt,
                                 extra=extra)

    resp = urllib.request.urlopen(url)
    encoding = resp.headers.get_content_charset()
    data = resp.read().decode(encoding)

    results = json.loads(data)['items']
    return results


def do_disambiguate(results):
    print('We found multiple results:\n')

    lines_pretty = [('\t{num}) {word} ({username}, {addtime})')
                    .format(num=i, word=r['original'],
                            addtime=r['standard_pronunciation']['addtime'],
                            username=r['standard_pronunciation']['username'])
                    for i, r in enumerate(results)]
    print('\n'.join(lines_pretty))

    response = int(input('\nChoose one: '))
    return results[response]


def do_download(result):
    url = result['standard_pronunciation']['pathmp3']
    # dest_filename = (unicodedata.normalize('NFKD', result['original'])
    #                  .encode('ascii', 'ignore'))
    dest_filename = '{}.mp3'.format(result['original'])

    with urllib.request.urlopen(url) as resp, open(dest_filename, 'wb') as dest:
        shutil.copyfileobj(resp, dest)


if __name__ == '__main__':
    config = parse_config(sys.argv)
    results = do_search(config)

    if len(results) == 0:
        print('No results found.')
        sys.exit(1)
    elif len(results) == 1:
        result = results[0]
    else:
        result = do_disambiguate(results)

    do_download(result)
