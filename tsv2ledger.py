#!/bin/python3
import argparse
import csv
import functools
import re
from collections import defaultdict
from collections import namedtuple

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


POSITIVE_AMOUNT_PATTERN = re.compile(r'([0-9\s]+),(\d\d)\s+(EUR|PLN|zł)')
NEGATIVE_AMOUNT_PATTERN = re.compile(r'\(([0-9\s]+),(\d\d)\)\s+(EUR|PLN|zł)')
ZERO_AMOUNT_PATTERN = re.compile(r'-\s+(EUR|PLN|zł)')


def amount_in_ledger_fmt(amount_in_source_fmt):
    """Convert a string representing amount field to a format used by "ledger"
    program.

    >>> amount_in_ledger_fmt('(2 099,49) zł')
    '-2,099.49 PLN'
    >>> amount_in_ledger_fmt('   -   zł')
    '0.00 PLN'
    >>> amount_in_ledger_fmt('3 999,99 EUR')
    '3,999.99 EUR'
    """
    currency_symbols = {'EUR': 'EUR', 'PLN': 'PLN', 'zł': 'PLN'}
    if match := POSITIVE_AMOUNT_PATTERN.search(amount_in_source_fmt):
        int_part, frac_part, currency = match.groups()
        int_part = int(remove_whitespace(int_part))
        symbol = currency_symbols[currency]
        return f'{int_part:,d}.{frac_part} {symbol}'
    if match := NEGATIVE_AMOUNT_PATTERN.search(amount_in_source_fmt):
        int_part, frac_part, currency = match.groups()
        int_part = int(remove_whitespace(int_part))
        symbol = currency_symbols[currency]
        return f'-{int_part:,d}.{frac_part} {symbol}'
    if match := ZERO_AMOUNT_PATTERN.search(amount_in_source_fmt):
        currency = match.group(1)
        symbol = currency_symbols[currency]
        return f'0.00 {symbol}'


def remove_whitespace(string):
    """Returns a string with all whitespace characters removed.

    >>> remove_whitespace('1 000\xa0\xa0777')
    '1000777'
    """
    return re.sub(r'\s', '', string)


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
    r"""Convert a string representing account specifier/fully qualified path
    to a format used by "ledger" program.

    >>> account_in_ledger_fmt(r'Cache\Current Assets\Assets')
    'Assets:Current Assets:Cache'
    """
    account_names = account_in_source_fmt.split('\\')
    account_names.reverse()
    return ':'.join(account_names)


def transactions_dict(tsv_file):
    rows = csv.DictReader(
        tsv_file,
        delimiter='\t',
        fieldnames=['ordinal', 'date', 'description', 'account',
                    'other_account', 'amount', 'is_posted']
    )
    next(rows)  # skip header
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
    parser = argparse.ArgumentParser(
            prog='tsv2ledger',
            description='Convert accounting journal from "tab separated '
                        'values" format to a format used by "ledger" program.'
                        )
    parser.add_argument(
            'tsv_file',
            help='A file with an accounting journal in tsv format. A row has '
                 'fields: ordinal number, date, description, account, other '
                 'account, amount. First row is a header row.')
    parser.add_argument(
            'dest_file',
            help='Name of the output file.')
    args = parser.parse_args()
    with open(args.tsv_file) as in_file:
        transactions = transactions_dict(in_file)
    with open(args.dest_file, 'wt') as out_file:
        for ordinal in sorted(transactions.keys()):
            rows = transactions[ordinal]
            date = rows[0].date
            description = rows[0].description
            transfers = [(row.account, row.amount) for row in rows]
            writeln = functools.partial(print, file=out_file)
            writeln(f'{date} {description}')
            writeln(indented(table(transfers, justify='l r', col_gap='  ')))
            writeln()
