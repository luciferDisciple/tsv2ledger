#!/bin/python3
import csv
import functools
import re
import sys
from collections import defaultdict
from collections import namedtuple
from datetime import date
from decimal import Decimal

CURRENCY = 'PLN'

JournalRow = namedtuple(
        'JournalRow',
        'ordinal date description account  amount'
)

def journal_row(row_dict):
    ordinal = int(row_dict['ordinal'])
    date = date_in_ledger_fmt(row_dict['date'])
    desc = row_dict['description']
    account = account_in_ledger_fmt(row_dict['account'])
    amount = amount_in_ledger_fmt(row_dict['amount'])
    return JournalRow(ordinal, date, desc, account, amount)

def amount_in_ledger_fmt(amount_in_source_fmt):
    """Convert a string representing amount field to a format used by "ledger"
    program.

    >>> amount_in_ledger_fmt('(2 099,49) zł')
    '-2099.49 PLN'
    """
    comma_separated_amount = re.sub('[^0-9,()]', '', amount_in_source_fmt)
    if comma_separated_amount.startswith('('):
        comma_separated_amount = '-' + comma_separated_amount[1:-1]
    dot_separated_amount = comma_separated_amount.replace(',', '.')
    return f'{dot_separated_amount} PLN'

def date_in_ledger_fmt(date_in_source_fmt):
    """Convert a string representing date to a format used by "ledger"
    program.

    >>> date_in_ledger_fmt('1 wrz 2022 (cz.)')
    '2022/09/01'
    """
    months = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze',
              'lip', 'sie', 'wrz', 'paź', 'lis', 'gru']
    day, month_name, year, *rest = date_in_source_fmt.split()
    day = int(day)
    month = months.index(month_name) + 1
    year = int(year)
    return f'{year}/{month:02}/{day:02}'

def account_in_ledger_fmt(account_in_source_fmt):
    """Convert a string representing account specifier/fully qualified path
    to a format used by "ledger" program.

    >>> account_in_ledger_fmt(r'Cache\Current Assets\Assets')
    'Assets:Current Assets:Cache'
    """
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
        fieldnames= ['ordinal', 'date', 'description', 'account',
                     'other_account', 'amount', 'is_posted']
    )
    header_row = next(rows)
    transactions = defaultdict(list)
    for row_dict in rows:
        row_tuple = journal_row(row_dict)
        transactions[row_tuple.ordinal].append(row_tuple)
    return transactions

def indented(text, width=4):
    r"""Return "text" with "width" number of spaces prepended to each line.
    
    >>> print(indented('1\n2\n3'))
        1
        2
        3
    """
    indent = ' ' * width
    indented_text = indent + text.replace('\n', '\n' + indent)
    return indented_text

def table(rows, justify, col_gap=' '):
    """Returns a string containg a rendering of "rows" as a table with columns
    justified according to justification scheme/spec in "justify" argument.
    Columns will be separated by "col_gap".

    >>> data = [
    ...    ('NAME', 'COUNTRY', 'LEVEL'),
    ...    ('John Doe', 'USA', '7'),
    ...    ('Geralt of Rivia', 'Temeria', '35'),
    ...    ('Guido van Rossum', 'Netherlands', '9,000')
    ... ]
    >>> print(table(data, 'l l r', col_gap='  '))
    NAME              COUNTRY      LEVEL
    John Doe          USA              7
    Geralt of Rivia   Temeria         35
    Guido van Rossum  Netherlands  9,000
    """
    columns = transposed(rows)
    transposed_result = []
    for col, justification in zip(columns, justify.split()):
        width = max(len(cell) for cell in col)
        transposed_column = []
        for cell in col:
            if justification == 'l':
                transposed_column.append(cell.ljust(width))
            elif justification == 'r':
                transposed_column.append(cell.rjust(width))
            else:
                raise ValueError('Text justification specifier not supported:'
                        f"'{justification}'")
        transposed_result.append(transposed_column)
    rows_with_justified_columns = transposed(transposed_result)
    result_lines = [
        col_gap.join(field) for field in rows_with_justified_columns
    ]
    return '\n'.join(result_lines)


def transposed(matrix):
    """Returns transposed 2-dimensional matrix (list of flat lists).

    >>> transposed([['a', 1, 'one'], ['b', 2, 'two'], ['c', 3, 'three']])
    [['a', 'b', 'c'], [1, 2, 3], ['one', 'two', 'three']]
    """
    transposed = []
    for column in zip(*matrix):
        transposed.append(list(column))
    return transposed

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Wrong number of arguments.')
        print_usage()
        exit(1)
    in_filename = sys.argv[1]
    out_filename = sys.argv[2]
    with open(in_filename) as in_file:
        transactions = transactions_dict(in_file)
    with open(out_filename, 'wt') as out_file:
        for ordinal in sorted(transactions.keys()):
            rows = transactions[ordinal]
            date = rows[0].date
            description = rows[0].description
            transfers = [(row.account, row.amount) for row in rows]
            writeln = functools.partial(print, file=out_file)
            writeln(f'{date} {description}')
            writeln(indented(table(transfers, justify='l r', col_gap='  ')))
            writeln()
