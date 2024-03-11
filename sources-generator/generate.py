#!/usr/bin/env python3

'''
This script generates Flatpak sources for IRPF apps on Flathub:

* https://github.com/search?q=org%3Aflathub+br.gov.fazenda.receita&type=repositories

These sources are composed of ZIP files, and upon extracting them, we get a single XML file, which
should be installed to the 'lib/resources' directory, where other XML files already exist.

These XML files are used by IRPF to keep its information database up to date, and they are updated
independently from the main app:

At start up, IRPF checks if they are up to date, and if they are not, it will download these ZIP
files and try to extract the XML files in them to the same location where 'irpf.jar' is.

However, on the Flatpak package, that location is write-protected, and so IRPF is not able to
perform the extraction successfully, leaving the program outdated.

So, the purpose of this tool is to include these updated XML files at the packaging stage.
'''

# Dependencies:
#
# - Python (>= 3.7): https://www.python.org/
# - defusedxml: https://pypi.org/project/defusedxml/
# - requests: https://pypi.org/project/requests/

# Usage:
#
# To generate the sources file, run:
# ./generate.py > generated-sources.yaml
#
# For more examples, run:
#
# ./generate.py -h

import argparse
import concurrent.futures
import textwrap

import hashlib
import logging
import os
import shlex
import sys

from dataclasses import dataclass
from xml.etree import ElementTree
import defusedxml.ElementTree as ET
import requests

XML_ASSETS_URL = 'https://downloadirpf.receita.fazenda.gov.br/irpf/{edition:d}/irpf/update/{path:s}'
JAVA_USER_AGENT = 'Java/11.0.22'

@dataclass
class ZIPFileIRPF:
    '''
    Details about a ZIP file used by IRPF
    '''
    id: str = None
    name: str = None
    url: str = None
    sha256: str = None
    size: int = -1

def validate_irpf_edition(edition: str) -> int:
    '''
    Validates an IRPF edition
    '''
    try:
        edition = int(edition)
    except ValueError as err:
        raise argparse.ArgumentTypeError('invalid IRPF edition, must be a number') from err

    if edition < 2020:
        raise argparse.ArgumentTypeError('editions prior to 2020 are not supported')

    return edition

def set_up_logging(level_index: int):
    '''
    Sets up logging output
    '''
    known_levels = ['INFO', 'DEBUG']
    level = known_levels[min(level_index, len(known_levels) - 1)]
    logging.basicConfig(level=level,
                        format='%(asctime)s [%(levelname)s] %(message)s')

def gen_zip_sources_url(edition: int, path='latest.xml') -> str:
    '''
    Generates an URL that points to an XML file that lists all the ZIP files
    '''
    return XML_ASSETS_URL.format(edition=edition, path=path)

def fetch_remote_url(url: str, headers=None) -> str | bytes:
    '''
    Makes an HTTP GET request to a remote URL, and returns the body of the response
    '''
    logging.debug('Fetching remote URL: %s', url)

    response = requests.get(url, timeout=30, allow_redirects=False, headers=headers)

    logging.debug('Response headers: %s', response.headers)
    logging.debug('Response body (truncated): %s', response.content[:300])

    response.raise_for_status()

    content_type = response.headers['Content-Type']

    return response.text if content_type.startswith('text/') else response.content

def text_to_xml(text: str) -> ElementTree.Element:
    '''
    Parse text as XML, using defusedxml
    '''
    return ET.fromstring(text)

def get_zips_from_xml(xml_obj: ElementTree.Element, edition: int) -> dict[ZIPFileIRPF]:
    '''
    Builds a detailed list about each ZIP file found in the specified XML object
    '''
    ids = []
    zips = []
    files = xml_obj.findall('.//extra/files/file')

    for i, file in enumerate(files):
        name = file.find('filePackageName')
        if name is None:
            logging.warning('<file> node #%d lacks a <filePackageName> child node.', i + 1)
            continue
        name = name.text

        if not name.endswith('.zip'):
            logging.warning('<file> node named "%s" is not a ZIP file.', name)
            continue

        _id = file.find('fileId')
        if _id is None:
            logging.warning('<file> node named "%s" lacks a "fileId" tag.', name)
            continue
        _id = _id.text

        assert _id not in ids, 'Duplicate file ID found, abort!'

        url = XML_ASSETS_URL.format(edition=edition, path=name)

        ids.append(_id)
        zips.append(ZIPFileIRPF(id=_id, name=name, url=url))

    zips = sorted(zips, key=lambda i: i.id)

    return zips

def download_and_hash_zip_files(files: dict[ZIPFileIRPF]) -> bool:
    '''
    Concurrently downloads a list of URLs of ZIP files in ``files``. If successful, the ``files``
    argument is modified to include each file's size (in bytes) and SHA256 sum.
    '''
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {}
        for index, file in enumerate(files):
            futures[executor.submit(fetch_remote_url, file.url,
                                                      headers = {
                                                        'User-Agent': JAVA_USER_AGENT
                                                      })] = index

        errors = 0
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            try:
                content = future.result()
            except requests.exceptions.HTTPError as err:
                logging.error('Failed to download remote ZIP file: %s | %s',
                               files[index].url, err)
                errors += 1
                continue

            size = len(content)
            assert size > 0, f'ZIP file is empty (0 bytes): {files[index].url}'

            sha256 = hashlib.sha256(content).hexdigest()

            files[index].sha256 = sha256
            files[index].size = size

        return errors == 0

def print_sources_file_signature():
    '''
    Prints a YAML-compatible comment, explaining how the sources list was generated
    '''
    script_name = os.path.basename(sys.argv[0])
    script_args = ' '.join(map(shlex.quote, sys.argv[1:]))

    print('# This sources list was generated by: '
          'https://github.com/guihkx/irpf-tools-flatpak/tree/master/sources-generator')
    print(f'# Command used: python {script_name} {script_args}\n')

def main():
    '''
    Entrypoint
    '''
    parser = argparse.ArgumentParser(description='Generates Flatpak sources for IRPF apps on '
                                                 'Flathub: https://flathub.org/apps/search?q=irpf')
    parser.add_argument('-d', '--direct-sources', action=argparse.BooleanOptionalAction,
                        default=False, help='generate direct sources, instead of extra-data ones')
    parser.add_argument('-e', '--edition', type=validate_irpf_edition, default=2023,
                        help='the IRPF edition of the ZIP files (defaults to 2023)')
    parser.add_argument('-n', '--no-data-checker', action=argparse.BooleanOptionalAction,
                        default=False, help='skip generation of x-checker-data entries '
                        '(https://github.com/flathub-infra/flatpak-external-data-checker)')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='enable debug output (very noisy)')

    options = parser.parse_args()
    set_up_logging(options.verbose)

    url_zip_src = gen_zip_sources_url(options.edition)
    logging.info('Fetching remote XML file: %s', url_zip_src)

    try:
        body = fetch_remote_url(url_zip_src,
                                headers={
                                    'User-Agent': JAVA_USER_AGENT
                                })
    except requests.exceptions.HTTPError as err:
        logging.error('Failed to fetch remote XML file: %s', err)
        if not options.verbose:
            logging.info('Hint: Rerun with -v for more details.')
        sys.exit(1)

    try:
        xml = text_to_xml(body)
    except ET.ParseError:
        logging.error('Failed to parse response body as XML.')
        if not options.verbose:
            logging.info('Hint: Rerun with -v for more details.')
        sys.exit(1)

    zip_files = get_zips_from_xml(xml, edition=options.edition)
    zip_total = len(zip_files)

    if zip_total == 0:
        logging.error('Found 0 (zero) ZIP files in the XML. Did its structure change?')
        if not options.verbose:
            logging.info('Hint: Rerun with -v for more details.')
        sys.exit(1)

    logging.info('Found %d ZIP files in the XML.', zip_total)
    logging.info('Downloading and hashing them...')

    if not download_and_hash_zip_files(zip_files):
        logging.error('Failed to download one or more ZIP files.')
        if not options.verbose:
            logging.info('Hint: Rerun with -v for more details.')
        sys.exit(1)

    logging.info('Outputting list of sources to standard output:')

    print_sources_file_signature()

    for k, zip_file in enumerate(zip_files):
        if options.direct_sources:
            source = f'''\
                   - type: archive
                     dest-filename: {zip_file.id}.zip
                     url: {zip_file.url}
                     sha256: {zip_file.sha256}
                     strip-components: 2'''
        else:
            source = f'''\
                   - type: extra-data
                     filename: {zip_file.id}.zip
                     url: {zip_file.url}
                     size: {zip_file.size}
                     sha256: {zip_file.sha256}'''

        if not options.no_data_checker:
            zip_url_tpl = XML_ASSETS_URL.format(edition=options.edition,
                                                path=f'{zip_file.id}__$version.zip')
            source += f'''
                     x-checker-data:
                       type: html
                       url: {url_zip_src}
                       version-pattern: {zip_file.id}__([\\d_]+)\\.zip
                       url-template: {zip_url_tpl}'''

        print(textwrap.indent(textwrap.dedent(source), '  '))
        if k + 1 < zip_total:
            print()

    logging.info('Done.')

if __name__ == '__main__':
    main()
