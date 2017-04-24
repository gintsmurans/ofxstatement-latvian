"""Parser implementation for Citadele generated statement reports"""

import re
import logging
from xml.etree import ElementTree

from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine


class CitadeleLVStatementParser(StatementParser):
    date_format = "%Y-%m-%d"

    statement = None
    fin = None  # file input stream

    debug = (logging.getLogger().getEffectiveLevel() == logging.DEBUG)

    def __init__(self, fin):
        self.statement = Statement()
        self.fin = fin

    def split_records(self):
        xml = ElementTree.parse(self.fin)
        xml = xml.getroot()

        namespaces = {'ns': xml.tag[1:].partition("}")[0]}
        statement = xml.find('ns:Statement', namespaces=namespaces)

        period = statement.find('ns:Period', namespaces=namespaces)
        self.statement.start_date = self.parse_datetime(period.find('ns:StartDate', namespaces=namespaces).text)
        self.statement.end_date = self.parse_datetime(period.find('ns:EndDate', namespaces=namespaces).text)

        account = statement.find('ns:AccountSet', namespaces=namespaces)
        if not self.statement.account_id:
            self.statement.account_id = account.find('ns:AccNo', namespaces=namespaces).text

        transactions = account.find('ns:CcyStmt', namespaces=namespaces)
        self.statement.start_balance = self.parse_float(transactions.find('ns:OpenBal', namespaces=namespaces).text)

        all_transactions = transactions.findall('ns:TrxSet', namespaces=namespaces)

        return all_transactions

    def parse_record(self, line):
        # Namespace stuff
        namespaces = {'ns': line.tag[1:].partition("}")[0]}

        # Get all fields
        type_code = line.find('ns:TypeCode', namespaces=namespaces).text
        date = line.find('ns:BookDate', namespaces=namespaces).text
        c_or_d = line.find('ns:CorD', namespaces=namespaces).text
        amount = line.find('ns:AccAmt', namespaces=namespaces).text
        id = line.find('ns:BankRef', namespaces=namespaces).text
        note = line.find('ns:PmtInfo', namespaces=namespaces).text

        # Payee name
        payee_name = None
        payee = line.find('ns:CPartySet', namespaces=namespaces)
        if payee:
            payee_account = payee.find('ns:AccHolder', namespaces=namespaces)
            if payee_account:
                payee_name = payee_account.find('ns:Name', namespaces=namespaces).text

        # Create statement line
        stmt_line = StatementLine(id, self.parse_datetime(date), note, self.parse_float(amount))
        stmt_line.payee = payee_name

        # Credit & Debit stuff
        stmt_line.trntype = "DEP"
        if c_or_d == 'D':
            stmt_line.amount = -stmt_line.amount
            stmt_line.trntype = "DEBIT"

        # Various types
        if type_code == 'CHOU':
            stmt_line.trntype = "ATM"
        elif type_code == 'MEMD':
            stmt_line.trntype = "SRVCHG"
        elif type_code == 'OUTP':
            stmt_line.trntype = "PAYMENT"
        elif type_code == 'INP':
            stmt_line.trntype = "XFER"

        # DEBUG
        if self.debug:
            print(stmt_line, stmt_line.trntype)

        return stmt_line

    def parse_float(self, value):
        return value if isinstance(value, float) else float(value.replace(',', '.'))


class CitadeleLVPlugin(Plugin):
    """Latvian Citadele CSV"""

    def get_parser(self, fin):
        parser = CitadeleLVStatementParser(fin)
        parser.statement.currency = self.settings.get('currency', 'EUR')
        return parser
