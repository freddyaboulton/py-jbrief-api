from ast import Str
from locale import strxfrm
from pydantic import BaseModel
from uuid import UUID


class ContestantBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    occupation: str
    city: str
    state: str


class QuestionBase(BaseModel):
    id: UUID
    game_id: int
    text: str
    answer: str
    category: str


class TurnBase(BaseModel):
    game_id: int
    contestant_id: int
    question_id: int
    clue_order_number: int
    change_in_score: float
    is_daily_double: bool
    is_final_jeopardy: bool