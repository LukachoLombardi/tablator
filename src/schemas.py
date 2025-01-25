from pydantic import BaseModel


class PassportModel(BaseModel):
    name: str
    surname: str
    birth_date: str
    passport_number: str
