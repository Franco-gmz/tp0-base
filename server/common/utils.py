import csv
import datetime
import logging
import time
from domain.agency_bet import AgencyBet

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574


""" A lottery bet registry. """
class Bet:
    def __init__(self, agency: str, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        agency must be passed with integer format.
        birthdate must be passed with format: 'YYYY-MM-DD'.
        number must be passed with integer format.
        """
        self.agency = int(agency)
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])

"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])

def store_agency_bets(bets: list[AgencyBet], agency) -> None:
    bet_collection = []
    for bet in bets:
        bet = Bet(agency, bet.name, bet.lastname, bet.dni, bet.birth_date, bet.bet_number)
        bet_collection.append(bet)
    store_bets(bet_collection)

def has_won_bet(agency_bet: AgencyBet) -> bool:
    try:
        bet = Bet("0", agency_bet.name, agency_bet.lastname, agency_bet.dni, agency_bet.birth_date, agency_bet.bet_number)
    except Exception as e:
        logging.info(
                "has_won_bet error con birt: %s and error: %s",
                agency_bet.birth_date, e
            )
    return has_won(bet)

def load_agency_bets() -> list[AgencyBet]:
    agency_bets = []

    for bet in load_bets():
        agency_bets.append(
            AgencyBet(
                bet.first_name,
                bet.last_name,
                bet.document,
                str(bet.birthdate),
                bet.number,
                bet.agency,
            )
        )

    return agency_bets