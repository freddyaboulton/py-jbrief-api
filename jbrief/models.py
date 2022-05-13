from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from typing import List


class Contestant(models.Model):
    id = fields.IntField(pk=True, index=True)
    first_name = fields.TextField()
    last_name = fields.TextField()
    occupation = fields.TextField()
    city = fields.TextField()
    state = fields.TextField()

    class Meta:
        table = "contestants"


class Question(models.Model):
    id = fields.CharField(pk=True, unique=True, index=True, max_length=32)
    text = fields.TextField()
    answer = fields.TextField()
    category = fields.TextField()

    class Meta:
        table = "questions"


class Turn(models.Model):
    id = fields.CharField(pk=True, unique=True, index=True, max_length=32)
    game_id = fields.IntField()
    order = fields.IntField()
    change_in_score = fields.FloatField()
    is_daily_double = fields.BooleanField()
    is_final_jeopardy = fields.BooleanField()

    contestant = fields.ForeignKeyField("models.Contestant", to_field="id")
    question = fields.ForeignKeyField("models.Question", to_field="id")

    class Meta:
        table = "turns"


ContestantBase = pydantic_model_creator(Contestant)
QuestionBase = pydantic_model_creator(Question)
TurnBase = pydantic_model_creator(Turn)


class GameBase(BaseModel):
    turns: List[TurnBase]
    contestants: List[ContestantBase]
    questions: List[QuestionBase]
