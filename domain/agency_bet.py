class AgencyBet:
    def __init__(self, name, lastname, dni, birth_date, bet_number):
        self.name = name
        self.lastname = lastname
        self.dni = dni
        self.birth_date = birth_date
        self.bet_number = bet_number

    @staticmethod
    def from_row(row: list):
        return AgencyBet(
            name=row[0],
            lastname=row[1],
            dni=row[2],
            birth_date=row[3],
            bet_number=int(row[4])
        )