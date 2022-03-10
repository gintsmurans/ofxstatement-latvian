"""Parser implementation for SEB generated statement reports"""

import re
import csv
import logging

from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import StatementLine, BankAccount


class SebLV_CSVStatementParser(CsvStatementParser):
    date_format = "%d.%m.%Y"
    card_purchase_re = re.compile(r".*#(\d+)$")

    debug = logging.getLogger().getEffectiveLevel() == logging.DEBUG
    accounts = {}

    def split_records(self):
        csv_file = csv.reader(self.fin.readlines(), delimiter=";", quotechar='"')
        return csv_file

    def parse_record(self, line):
        # Skip header line and account number lines
        if self.cur_record <= 2 or len(line) < 19:
            return None

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
        from_account_id = line[6]
        from_bank_name = line[7]
        from_bank_code = line[8]
        account_id = line[16]

        if not self.statement.account_id:
            self.statement.account_id = account_id
            self.accounts[account_id] = BankAccount("AS \"SEB banka\"", account_id)
            self.accounts[account_id].branch_id = "UNLALV2X"

        if from_account_id and not from_account_id in self.accounts:
            self.accounts[from_account_id] = BankAccount(from_bank_name, from_account_id)
            self.accounts[from_account_id].branch_id = from_bank_code

        # Convert LVL to EUR
        if currency == "LVL":
            currency = "EUR"
            amount = round(float(amount) / 0.702804, 2)

        # Create a statement line
        stmt_line = StatementLine(
            id, self.parse_datetime(date), note, self.parse_float(amount)
        )
        stmt_line.payee = payee_name
        stmt_line.refnum = refnum
        stmt_line.date_user = self.parse_datetime(date_user)

        # Received from or sent to bank
        if account_id:
            stmt_line.bank_account_to = self.accounts[account_id]

        # Credit & Debit stuff
        stmt_line.trntype = "DEP"
        if c_or_d == "D":
            stmt_line.amount = -stmt_line.amount
            stmt_line.trntype = "DEBIT"

            if from_account_id:
                stmt_line.bank_account_to = self.accounts[from_account_id]
            else:
                stmt_line.bank_account_to = None

        # Various types
        if "PMNTCCRDCWDL" in type_code:
            stmt_line.trntype = "ATM"
        elif "ACMTMDOPFEES" in type_code:
            stmt_line.trntype = "SRVCHG"
        elif "LDASCSLNINTR" in type_code:
            stmt_line.trntype = "INT"
        elif "PMNTCCRDOTHR" in type_code:
            stmt_line.trntype = "PAYMENT"
            m = self.card_purchase_re.match(stmt_line.memo)
            if m:
                # This is an electronic purchase. Extract check number from the memo field
                stmt_line.check_no = m.group(1)

        elif "PMNTRCDTESCT" in type_code or "PMNTICDTESCT" in type_code:
            stmt_line.trntype = "XFER"

        # DEBUG
        if self.debug:
            print(stmt_line, stmt_line.trntype)

        return stmt_line

    def parse_float(self, value):
        return value if isinstance(value, float) else float(value.replace(",", "."))


class SebLVPlugin(Plugin):
    """Latvian SEB CSV"""

    def get_parser(self, fin):
        encoding = self.settings.get("charset", "utf-8")
        f = open(fin, "r", encoding=encoding)
        parser = SebLV_CSVStatementParser(f)
        parser.statement.currency = self.settings.get("currency", "EUR")
        return parser
