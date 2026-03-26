import argparse
from .data import download_MIP
from .data import download_regions

def main():
    '''
    Defines command line utilities for this package, including:

    OCO_v11MIP_analysis download [dataset] --force [force]
    '''

    parser     = argparse.ArgumentParser(prog='OCO_v11MIP_analysis')
    subparsers = parser.add_subparsers(dest='command')

    dl = subparsers.add_parser('download', 
                               help='Download datasets')
    dl.add_argument('dataset',
                    choices = ['MIP', 'region', 'aggregate']
                    help='Dataset to download')
    dl.add_argument('--force', action='store_true', 
                    help='Redownload even if exists')

    args.parser.parse_args()
    if(args.command == 'download'):
        download_MIP(dataset=args.dataset, force=args.force)
    else:
        parser.print_help()
