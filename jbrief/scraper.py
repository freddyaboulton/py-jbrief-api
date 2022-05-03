from urllib.request import urlopen
from bs4 import BeautifulSoup, Tag
from jbrief.models import ContestantBase, QuestionBase, TurnBase
import re
import uuid

from typing import List, Tuple, Dict


def get_contestants(html: BeautifulSoup, game_id: int) -> Tuple[List[ContestantBase], List[str]]:
    info_template = "(?P<first_name>[A-Za-z]*) (?P<last_name>[A-za-z]*), a[n]? (?P<occupation>.[A-Za-z ]*) from (?P<city>.[a-zA-Z]*), (?P<state>.[a-zA-Z]*)[*]?"
    id_template = ".*=(?P<id>[0-9]*)"
    contestants_html = html.findAll('p', {'class': 'contestants'})
    contestants = []
    errors = []
    for i, contestant_html in enumerate(contestants_html):
        id_match = re.match(id_template, contestant_html.find("a")['href'])
        info_match = re.match(info_template, contestant_html.text)
        try:
            contestants.append(ContestantBase(id=id_match.group("id"), first_name=info_match.group("first_name"),
                                               last_name=info_match.group("last_name"),
                                               occupation=info_match.group("occupation"),
                                               city=info_match.group("city"),
                                               state=info_match.group("state")))
        except AttributeError:
            errors.append(f"Cannot parse info for contestant {i} of game {game_id}")
    return contestants, errors


def category_from_clue_id(clue_id: str, categories) -> str:
    if "FJ" in clue_id:
        return categories[-1]
    offset = 5 if "DJ" in clue_id else 0
    return categories[offset + int(clue_id.split("_")[2])]


def get_order_from_clue_id(clue_id: str, order_number: int, last_jeopardy_clue: int):
    return order_number if "DJ" not in clue_id else order_number + last_jeopardy_clue


def get_questions(html: BeautifulSoup, game_id: int) -> Tuple[List[QuestionBase], List[str]]:
    categories = [c.text for c in html.findAll('td', {'class': 'category_name'})]
    if len(categories) != 13:
        return [f"Cannot parse questions because cant parse categories"]
    
    # Skip FJ
    clues_html: List[Tag] = html.findAll('td', {'class': 'clue'})[:-1]
    clues_html += [html.find('table',{'class':'final_round'})]
    questions = []
    errors = []

    for i, clue in enumerate(clues_html):
        try:
            text_html = clue.findChild("td", {'class': "clue_text"})
            category = category_from_clue_id(text_html["id"], categories)
            clue_text = text_html.text
            clue_id = uuid.uuid4()
            answer = BeautifulSoup(clue.findChild("div")['onmouseover'], 'html5').findChild("em", {"class": "correct_response"}).text
            questions.append(QuestionBase(id=clue_id, game_id=game_id, text=clue_text, answer=answer, category=category))
        except Exception as e:
            errors.append(f"Cannot parse clue {i} of game {game_id} because of {str(e)}")
    
    return questions, errors


def str_to_float(string) -> float:
    return float(string[string.find("$") + 1:].replace(",", ""))


def get_clue_value(clue: Tag) -> Tuple[float, bool]:
    dd_html = clue.findChild("td", {"class": "clue_value_daily_double"})
    if dd_html is not None:
        value_text = dd_html.text
        is_dd = True
    else:
        value_text = clue.findChild("td", {"class": "clue_value"}).text
        is_dd = False
    return str_to_float(value_text), is_dd


def get_max_single_jeopardy_clue_order(clues: List[Tag]) -> int:
    max_single_jeopardy_clue = -1
    for c in clues:
        order_number_html = c.find("td", {"class": "clue_order_number"})
        clue_text_html = c.find("td", {"class": "clue_text"})
        if order_number_html is not None and clue_text_html is not None:
            if int(order_number_html.text) > max_single_jeopardy_clue and "DJ" not in clue_text_html.text:
                max_single_jeopardy_clue = int(order_number_html.text)
    return max_single_jeopardy_clue


def get_turns(html: BeautifulSoup, game_id: int,
              contestant_name_to_id: Dict[str, int],
              question_text_to_id: Dict[str, id]) -> Tuple[List[TurnBase], List[str]]:
    clues_html: List[Tag] = html.findAll('td', {'class': 'clue'})[:-1]
    turns: List[TurnBase] = []
    errors: List[str] = []
    single_jeopary_end = get_max_single_jeopardy_clue_order(clues_html)
    for i, clue in enumerate(clues_html):
        try:
            clue_text = clue.findChild("td", {'class': "clue_text"})
            value, is_dd = get_clue_value(clue)
            order = get_order_from_clue_id(clue_text["id"],
                                           int(clue.findChild("td", {'class': "clue_order_number"}).text),
                                           single_jeopary_end)
            wrong = [t.text for t in BeautifulSoup(clue.findChild("div")['onmouseover'], 'html5').findChildren("td", {"class": "wrong"})]
            text = clue_text.text
            if 'Triple Stumper' in wrong:
                wrong_turns = [TurnBase(game_id=game_id, contestant_id=cid_,
                                        question_id=question_text_to_id[text],
                                        order=order,
                                        change_in_score=-value,
                                        is_daily_double=is_dd,
                                        is_final_jeopardy=False) for cid_ in contestant_name_to_id.values()]
                correct_turns = []
            else:
                wrong_turns = [TurnBase(game_id=game_id,
                                        contestant_id=contestant_name_to_id[name],
                                        question_id=question_text_to_id[text],
                                        order=order,
                                        change_in_score=-value,
                                        is_daily_double=is_dd,
                                        is_final_jeopardy=False) for name in wrong]
                correct = [t.text for t in BeautifulSoup(clue.findChild("div")['onmouseover'], 'html5').findChildren("td", {"class": "right"})]
                correct_turns = [TurnBase(game_id=game_id,
                                          contestant_id=contestant_name_to_id[name],
                                          question_id=question_text_to_id[text],
                                          order=order,
                                          change_in_score=value,
                                          is_daily_double=is_dd,
                                          is_final_jeopardy=False) for name in correct]
            turns.extend(wrong_turns + correct_turns)
        except Exception as e:
            errors.append(f"Can't parse turn {i} because {str(e)}")
    final_jeopardy = html.find('table', {'class':'final_round'})
    try:
        fj_order = turns[-1].order + 1
        fj_text = final_jeopardy.find("td", {'class': "clue_text"}).text
        rows = BeautifulSoup(final_jeopardy.findChild("div")['onmouseover'], 'html5').findAll("td")
        rows = [rows[i:i+3] for i in range(0, len(rows), 3)]
        for contestant_html, _, wager_html in rows:
            contestant_id = contestant_name_to_id[contestant_html.text]
            value = str_to_float(wager_html.text)
            if contestant_html['class'] == ['wrong']:
                value *= -1
            turns.append(TurnBase(game_id=game_id,
                                contestant_id=contestant_id,
                                question_id=question_text_to_id[fj_text],
                                order=fj_order,
                                change_in_score=value,
                                is_daily_double=False,
                                is_final_jeopardy=True))
    except Exception as e:
        errors.append(f"Can't parse FJ because {str(e)}")        

    return turns, errors

    

if __name__ == "__main__":
    html = BeautifulSoup(urlopen("https://j-archive.com/showgame.php?game_id=7343"), "html5")
    contestants, e = get_contestants(html, 7343)
    print(contestants)
    print(e)
    questions, e_q = get_questions(html, 7343)
    print(questions)
    name_to_id = {c.first_name: c.id for c in contestants}
    text_to_id = {q.text: q.id for q in questions}
    turns, e_t = get_turns(html, 7343, name_to_id, text_to_id)
    print(turns)
    print(e_t)


