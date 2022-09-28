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

def journal_row(raw_journal_row):
    ordinal = int(raw_journal_row)
    date = date_from(raw_journal_row.date)
    desc = raw_journal_row.description
    account = account_from(raw_journal_row.account)
    other_account = account_from(raw_journal_row.other_account)
    amount = amount_from(raw_journal_row.amount)
    return JournalRow(ordinal, date, desc, account, other_account, amount)

def amount_from(formatted_money_amount):
    '''>>> amount_from('-2 099,49 zł')
    Decimal('-2099.49')
    '''
    comma_separated_amount = re.sub('[^0-9,-]', '', formatted_money_amount)
    dot_separated_amount = comma_separated_amount.replace(',', '.')
    return Decimal(dot_separated_amount)

def date_from(formatted_date):
    '''>>> date_from('28 wrz 2022 (śr.)')
    datetime.date(2022, 9, 28)
    '''
    months = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze',
              'lip', 'sie', 'wrz', 'paź', 'lis', 'gru']
    day, month_name, year, *rest = formatted_date.split()
    day = int(day)
    month = months.index(month_name) + 1
    year = int(year)
    return date(year, month, day)

def account_from(formatted_account):
    '''>>> account_from(r'Cache\Current Assets\Assets')
    'Assets:Current Assets:Cache'
    '''
    sub_accounts = formatted_account.split('\\')
    sub_accounts.reverse()
    return ':'.join(sub_accounts)

def print_usage():
    exec_name = sys.argv[0]
    print(f'usage: {exec_name} TSV_FILE DEST_FILE')
    print('Convert accounting journal from "tab separated values" format to')
    print('a format used by "ledger" program.')

def transactions_dict(tsv_file):
    header_row = next(file)
    transactions = defaultdict(list)
    for fields in csv.reader(tsv_file, delimiter='\t'):
        journal_row = RawJournalRow(*fields)
        transactions[journal_row.ordinal].append(journal_row)
    return transactions

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Wrong number of arguments.')
        print_usage()
        exit(1)
    in_filename = sys.argv[1]
    out_filename = sys.argv[2]
    print('Not yet implemented...')
