from jbrief.db import init_db
from fastapi import FastAPI
from jbrief.models import Question, QuestionBase, Contestant, ContestantBase, Turn, TurnBase, GameBase
from tortoise.queryset import Q
from tortoise.contrib.fastapi import HTTPNotFoundError
from typing import List
import uvicorn

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    init_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")


@app.get(
    "/question/{question_id}", response_model=QuestionBase, responses={404: {"model": HTTPNotFoundError}}
)
async def get_question(question_id: str) -> QuestionBase:
    return await QuestionBase.from_queryset_single(Question.get(id=question_id))


@app.get(
    "/contestant/{contestant_id}", response_model=ContestantBase, responses={404: {"model": HTTPNotFoundError}}
)
async def get_contestant(contestant_id: int) -> ContestantBase:
    return await ContestantBase.from_queryset_single(Contestant.get(id=contestant_id))


@app.get(
    "/turn/{turn_id}", response_model=TurnBase, responses={404: {"model": HTTPNotFoundError}}
)
async def get_turn(turn_id: str) -> ContestantBase:
    return await TurnBase.from_queryset_single(Turn.get(id=turn_id))


@app.get(
    "/contestant/game/{game_id}", response_model=List[ContestantBase], responses={404: {"model": HTTPNotFoundError}}
)
async def get_contestants_for_game(game_id: int) -> List[ContestantBase]:
    contestants = await Turn.filter(game_id=game_id).distinct().values("contestant_id")
    return await ContestantBase.from_queryset(Contestant.filter(Q(id__in=[c["contestant_id"] for c in contestants])))


@app.get("/game/{game_id}", response_model=GameBase)
async def get_game(game_id: int) -> GameBase:
    all_turns = await Turn.filter(game_id=game_id).prefetch_related("contestant", "question")

    contestants = set([t.contestant for t in all_turns])
    contestants = [await ContestantBase.from_tortoise_orm(c) for c in contestants]

    questions = set([t.question for t in all_turns])
    questions = [await QuestionBase.from_tortoise_orm(q) for q in questions]

    return GameBase(turns=all_turns, questions=questions, contestants=contestants)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
