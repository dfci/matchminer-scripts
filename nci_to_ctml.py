#!/usr/bin/env python2

"""
SYNOPSIS

    This script will accept a clinical trial's NCT ID, a comma-separated list
    of NCT IDs, or a file containing a comma-separated list of NCT IDs,
    query the NCI Clinical Trials API, and output a CTML file in YAML format
    containing all information returned by the NCI API.

    NCI Clinical Trials API documentation is available here:
    https://clinicaltrialsapi.cancer.gov/

EXAMPLES
    ./nci_to_ctml.py \
        -i NCT02194738 \
        -o ${output_directory}

    - to remove fields returned by NCI's CT API but that you want excluded from the CTML file:
        ./nci_to_ctml.py \
            -i NCT02194738 \
            -o ${output_directory} \
            --remove-fields sites,arms

AUTHOR
    Zachary Zwiesler <zwiesler@jimmy.harvard.edu> (Nov 2017)
"""

import os
import sys
import yaml
import time
import requests
import argparse
import datetime as dt


address = 'https://clinicaltrialsapi.cancer.gov/v1/clinical-trials'


def main(opts):

    nctids = []
    if os.path.isfile(opts.inpath):
        with open(opts.inpath, 'r') as f:
            for line in f.readlines():
                nctids.extend([i for i in line.strip().split(',') if i])
    else:
        nctids.extend(opts.inpath.split(','))

    # error handling
    if not os.path.isdir(opts.outpath):
        print '## ERROR: Output directory %s not found.\n' \
              '##        Please specify the output directory you would prefer\n' \
              '##        or leave unset to write to your current working directory.\n' % opts.outpath
        sys.exit(0)

    if all(not i.upper().startswith('NCT') for i in nctids):
        print '## ERROR: There are no valid NCT IDs in your list. All IDs should start\n' \
              '##        with the characters "NCT". Aborting script.'
        sys.exit(0)

    for nctid in nctids:

        if not nctid.upper().startswith('NCT'):
            print '\n## WARNING: "%s" is not a valid NCT ID. All IDs should start' % nctid
            print '##          with the characters "NCT". This trial will be skipped.\n'
            continue

        # API request
        params = '?nct_id=%s' % nctid
        url = address + params

        try:
            r = requests.get(url)
        except:
            time.sleep(1)
            r = requests.get(url)

        if r.status_code != 200 or 'trials' not in r.json():
            print '\n## WARNING: API request %s was unsuccessful. \n' \
                  '## %s\n' % (url, r.content)
            continue

        data = r.json()['trials']
        if len(data) == 0:
            print '\n## WARNING: Trial not found: %s\n' % nctid
            continue

        # Write CTML
        data = data[0]
        if opts.remove_fields:
            for field in opts.remove_fields.split(','):
                if field in data:
                    del data[field]

        filename = '%s/%s.yml' % (opts.outpath, nctid.upper())
        with open(filename, 'w') as ff:
            yaml.safe_dump(data, ff, default_flow_style=False)

        print '## INFO: Successfully wrote CTML file for %s' % nctid.upper()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='inpath', required=True,
                        help='Specify an NCT ID, a comma-separated list of NCT IDs, or the '
                             'path to a file containing a comma-separated list of NCT IDs.')
    parser.add_argument('-o', dest='outpath', default=os.getcwd(),
                        help='Specify the output path of your CTML files. Defaults to your '
                             'current working directory.')
    parser.add_argument('--remove-fields', dest='remove_fields', required=False,
                        help='Optionally specify a comma-separated list of NCI CT fields'
                             'you would like to exclude from the final CTML.')
    parser.set_defaults(func=main)

    args = parser.parse_args()
    args.func(args)

    print "##", "-" * 50
    print '##', 'Execution complete on %s.' % dt.datetime.now().strftime('%b-%d-%Y %X')
    print '##', 'CTML files written to %s' % args.outpath
    print "##", "-" * 50
