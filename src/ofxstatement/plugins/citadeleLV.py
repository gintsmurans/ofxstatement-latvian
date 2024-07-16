"""Parser implementation for Citadele generated statement reports"""

import logging
from decimal import Decimal
from xml.etree import ElementTree

from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import StatementLine


class CitadeleLVStatementParser(StatementParser[ElementTree.Element]):
    date_format: str = "%Y-%m-%d"

    filename: str | None
    debug: bool

    def __init__(self, filename: str):
        super().__init__()

        self.filename = filename
        self.debug = logging.getLogger().getEffectiveLevel() == logging.DEBUG

    def split_records(self) -> list[ElementTree.Element]:
        assert self.filename is not None, "No input file provided"

        xml = ElementTree.parse(self.filename)
        xml = xml.getroot()

        # Namespace stuff
        namespaces = {"ns": xml.tag[1:].partition("}")[0]}
        statement = xml.find("ns:Statement", namespaces=namespaces)
        if statement is None:
            raise Exception("No statement found in XML")

        # Find the period
        period = statement.find("ns:Period", namespaces=namespaces)
        if period is not None:
            start_date = period.find("ns:StartDate", namespaces=namespaces)
            if start_date is not None and start_date.text is not None:
                self.statement.start_date = self.parse_datetime(start_date.text)

            end_date = period.find("ns:EndDate", namespaces=namespaces)
            if end_date is not None and end_date.text is not None:
                self.statement.end_date = self.parse_datetime(end_date.text)

        # Find the account
        account = statement.find("ns:AccountSet", namespaces=namespaces)
        if account is None:
            raise Exception("No account found in XML")

        account_id = account.find("ns:AccNo", namespaces=namespaces)
        if not self.statement.account_id and account_id is not None:
            self.statement.account_id = account_id.text

        # Find all transactions
        transactions = account.find("ns:CcyStmt", namespaces=namespaces)
        if transactions is None:
            raise Exception("No transaction tag found in XML")
        all_transactions = transactions.findall("ns:TrxSet", namespaces=namespaces)

        # Find the opening and closing balances which are stored in transactions
        opening_balance = transactions.find("ns:OpenBal", namespaces=namespaces)
        if opening_balance is not None and opening_balance.text is not None:
            self.statement.start_balance = Decimal(
                self.parse_float(opening_balance.text)
            )

        closing_balance = transactions.find("ns:CloseBal", namespaces=namespaces)
        if closing_balance is not None and closing_balance.text is not None:
            self.statement.end_balance = Decimal(self.parse_float(closing_balance.text))

        return all_transactions

    def parse_record(self, line: ElementTree.Element) -> StatementLine:
        # Namespace stuff
        namespaces = {"ns": line.tag[1:].partition("}")[0]}

        # Gather all the fields
        type_code = line.find("ns:TypeCode", namespaces=namespaces)
        if type_code is None or type_code.text is None:
            raise Exception("No type code found in XML")
        type_code = type_code.text

        date_el = line.find("ns:BookDate", namespaces=namespaces)
        if date_el is None or date_el.text is None:
            raise Exception("No date found in XML")
        date = self.parse_datetime(date_el.text)

        c_or_d = line.find("ns:CorD", namespaces=namespaces)
        if c_or_d is None or c_or_d.text is None:
            raise Exception("No credit/debit found in XML")
        c_or_d = c_or_d.text

        amount_el = line.find("ns:AccAmt", namespaces=namespaces)
        if amount_el is None or amount_el.text is None:
            raise Exception("No amount found in XML")
        amount = Decimal(self.parse_float(amount_el.text))

        bank_ref = line.find("ns:BankRef", namespaces=namespaces)
        if bank_ref is not None:
            bank_ref = bank_ref.text

        note = line.find("ns:PmtInfo", namespaces=namespaces)
        if note is not None:
            note = note.text

        # Find payee name
        payee_name: str | None = None
        payee = line.find("ns:CPartySet", namespaces=namespaces)
        if payee:
            payee_account = payee.find("ns:AccHolder", namespaces=namespaces)
            if payee_account:
                payee_name_el = payee_account.find("ns:Name", namespaces=namespaces)
                if payee_name_el:
                    payee_name = payee_name_el.text

        # Create statement line
        stmt_line = StatementLine(bank_ref, date, note, amount)
        stmt_line.payee = payee_name

        # Credit & Debit stuff
        stmt_line.trntype = "DEP"
        if c_or_d == "D":
            stmt_line.amount = -amount
            stmt_line.trntype = "DEBIT"

        # Various types
        if type_code == "CHOU":
            stmt_line.trntype = "ATM"
        elif type_code == "MEMD":
            stmt_line.trntype = "SRVCHG"
        elif type_code == "OUTP":
            stmt_line.trntype = "PAYMENT"
        elif type_code == "INP":
            stmt_line.trntype = "XFER"

        # DEBUG
        if self.debug:
            print(stmt_line, stmt_line.trntype)

        return stmt_line

    def parse_float(self, value: str) -> Decimal:
        if isinstance(value, float):
            value = str(value)

        # Fix latvian decimal separator thing
        value = value.replace(",", ".")

        return super().parse_float(value)


class CitadeleLVPlugin(Plugin):
    """Latvian Citadele CSV"""

    def get_parser(self, filename: str) -> CitadeleLVStatementParser:
        parser = CitadeleLVStatementParser(filename)
        parser.statement.currency = self.settings.get("currency", "EUR")
        return parser
