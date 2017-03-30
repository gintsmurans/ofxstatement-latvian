"""Parser implementation for SEB generated statement reports"""

import re
import csv

from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine


class SebLV_CSVStatementParser(CsvStatementParser):
    date_format = "%d.%m.%Y"
    card_purchase_re = re.compile(r".*#(\d+)$")

    def split_records(self):
        csv_file = csv.reader(self.fin.readlines(), delimiter=';', quotechar='"')
        return csv_file

    def parse_record(self, line):
        if self.cur_record <= 2:
            # Skip header line
            return None

        if not self.statement.account_id:
            self.statement.account_id = line[16]

        # Get all fields
        type_code = line[12]
        date = line[1]
        date_user = line[11]
        c_or_d = line[14]
        amount = self.parse_float(line[3])
        id = line[10]
        refnum = line[10]
        note = line[9]
        payee_name = line[4]
        currency = line[17]

        # Convert LVL to EUR
        if currency == 'LVL':
            currency = 'EUR'
            amount = round(float(amount) / 0.702804, 2)

        # Create a statement line
        stmt_line = StatementLine(id, self.parse_datetime(date), note, self.parse_float(amount))
        stmt_line.payee = payee_name
        stmt_line.refnum = refnum
        stmt_line.date_user = self.parse_datetime(date_user)

        # Credit & Debit stuff
        stmt_line.trntype = "DEP"
        if c_or_d == 'D':
            stmt_line.amount = -stmt_line.amount
            stmt_line.trntype = "DEBIT"

        # Various types
        if 'PMNTCCRDCWDL' in type_code:
            stmt_line.trntype = "ATM"
        elif 'ACMTMDOPFEES' in type_code:
            stmt_line.trntype = "SRVCHG"
        elif 'LDASCSLNINTR' in type_code:
            stmt_line.trntype = "INT"
        elif 'PMNTCCRDOTHR' in type_code:
            stmt_line.trntype = "PAYMENT"
            m = self.card_purchase_re.match(stmt_line.memo)
            if m:
                # This is an electronic purchase. Extract check number from the memo field
                stmt_line.check_no = m.group(1)

        elif 'PMNTRCDTESCT' in type_code or 'PMNTICDTESCT' in type_code:
            stmt_line.trntype = "XFER"

        # Print for testing purposes and return our converted statement line
#         print(stmt_line, stmt_line.trntype)
        return stmt_line

    def parse_float(self, value):
        return value if isinstance(value, float) else float(value.replace(',', '.'))


class SebLVPlugin(Plugin):
    """Latvian SEB CSV"""

    def get_parser(self, fin):
        f = open(fin, "r")
        parser = SebLV_CSVStatementParser(f)
        parser.statement.currency = self.settings.get('currency', 'EUR')
        return parser
