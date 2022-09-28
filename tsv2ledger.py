#!/bin/python3
import csv
import re
import sys
from collections import defaultdict
from collections import namedtuple
from datetime import date
from decimal import Decimal

CURRENCY = 'PLN'

RawJournalRow = namedtuple(
        'RawJournalRow',
        'ordinal date description account other_account amount is_posted'
)

JournalRow = namedtuple(
        'JournalRow',
        'ordinal date description account other_account amount'
)

def journal_row(row_dict):
    ordinal = int(row_dict['ordinal'])
    date = date_in_ledger_fmt(row_dict['date'])
    desc = row_dict['description']
    account = account_in_ledger_fmt(row_dict['account'])
    other_account = account_in_ledger_fmt(row_dict['other_account'])
    amount = amount_in_ledger_fmt(row_dict['amount'])
    return JournalRow(ordinal, date, desc, account, other_account, amount)

def amount_in_ledger_fmt(amount_in_source_fmt):
    '''>>> amount_in_ledger_fmt('(2 099,49) zł')
    '-2099.49 PLN'
    '''
    comma_separated_amount = re.sub('[^0-9,()]', '', amount_in_source_fmt)
    if comma_separated_amount.startswith('('):
        comma_separated_amount = '-' + comma_separated_amount[1:-1]
    dot_separated_amount = comma_separated_amount.replace(',', '.')
    return f'{dot_separated_amount} CURRENCY'

def date_in_ledger_fmt(date_in_source_fmt):
    '''>>> date_in_ledger_fmt('1 wrz 2022 (cz.)')
    '2022/09/01'
    '''
    months = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze',
              'lip', 'sie', 'wrz', 'paź', 'lis', 'gru']
    day, month_name, year, *rest = date_in_source_fmt.split()
    day = int(day)
    month = months.index(month_name) + 1
    year = int(year)
    return f'{year}/{month:02}/{day:02}'

def account_in_ledger_fmt(account_in_source_fmt):
    '''>>> account_in_ledger_fmt(r'Cache\Current Assets\Assets')
    'Assets:Current Assets:Cache'
    '''
    account_names = account_in_source_fmt.split('\\')
    account_names.reverse()
    return ':'.join(account_names)

def print_usage():
    exec_name = sys.argv[0]
    print(f'usage: {exec_name} TSV_FILE DEST_FILE')
    print('Convert accounting journal from "tab separated values" format to')
    print('a format used by "ledger" program.')

def transactions_dict(tsv_file):
    rows = csv.DictReader(
        tsv_file,
        delimiter='\t',
        fieldnames= ['ordinal', 'date', 'description', 'account', 'other_account', 'amount', 'is_posted']
    )
    header_row = next(rows)
    transactions = defaultdict(list)
    for row_dict in rows:
        row_tuple = journal_row(row_dict)
        transactions[row_tuple.ordinal].append(row_tuple)
    return transactions

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Wrong number of arguments.')
        print_usage()
        exit(1)
    in_filename = sys.argv[1]
    out_filename = sys.argv[2]
    print('Not yet implemented...')
