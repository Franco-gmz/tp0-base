from domain.agency_bet import AgencyBet

def serialize_bet(bet: AgencyBet) -> bytes:
    data = f"{bet.name}|{bet.lastname}|{bet.dni}|{bet.birth_date}|{bet.bet_number}"
    return data.encode("utf-8")

def deserialize_bet(data: bytes) -> AgencyBet:
    decoded = data.decode("utf-8")
    parts = decoded.split("|")

    if len(parts) != 5:
        raise ValueError("Invalid bet format")

    return AgencyBet(
        name=parts[0],
        lastname=parts[1],
        dni=parts[2],
        birth_date=parts[3],
        bet_number=int(parts[4])
    )