from pydantic import BaseModel


class TicketCreate(BaseModel):
    content: str
