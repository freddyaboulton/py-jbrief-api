from urllib.request import urlopen
from bs4 import BeautifulSoup, Tag
from .models import ContestantBase, QuestionBase
import re
import uuid

from typing import List, Tuple


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
            contestants.append(ContestantBase(id_match.group("id"), *info_match.groups()))
        except AttributeError:
            errors.append(f"Cannot parse info for contestant {i} of game {game_id}")
    return contestants, errors


def category_from_clue_id(clue_id: str, categories) -> str:
    if "FJ" in clue_id:
        return categories[-1]
    offset = 5 if "DJ" in clue_id else 0
    return categories[offset + int(clue_id.split("_")[2])]


def get_questions(html: BeautifulSoup, game_id: int) -> Tuple[List[QuestionBase], List[str]]:
    categories = [c.text for c in html.findAll('td', {'class': 'category_name'})]
    if len(categories) != 13:
        return [f"Cannot parse questions because cant parse categories"]
    
    clues_html: List[Tag] = html.findAll('td', {'class': 'clue'})
    questions = []
    errors = []
    # Skip FJ
    for i, clue in enumerate(clues_html[:-1]):
        try:
            text_html = clue.findChild("td", {'class': "clue_text"})
            category = category_from_clue_id(text_html["id"], categories)
            clue_text = text_html.text
            clue_id = uuid.uuid4()
            answer = BeautifulSoup(clue.findChild("div")['onmouseover'], 'html5').findChild("em", {"class": "correct_response"}).text
            questions.append(QuestionBase(id=clue_id, game_id=game_id, text=clue_text, answer=answer, category=category))
        except Exception as e:
            errors.append(f"Cannot parse clue {i} of game {game_id} because of {str(e)}")
    
    try:
        fj_html = html.find('table',{'class':'final_round'})
        fj_text_html = fj_html.findChild("td", {"class": "clue_text"})
        fj_category = category_from_clue_id(fj_html['id'], categories)
        fj_text = fj_text_html.text
        fj_id = uuid.uuid4()
        answer = BeautifulSoup(fj_html.findChild("div")['onmouseover'], 'html5').findChild("em", {"class": "correct_response"}).text
        questions.append(QuestionBase(id=fj_id, game_id=game_id, text=fj_text, answer=answer, category=fj_category))
    except Exception as e:
        errors.append(f"Cannot parse clue {i} of game {game_id} because of {str(e)}")


if __name__ == "__main__":
    html = BeautifulSoup(urlopen("https://j-archive.com/showgame.php?game_id=7343"), "html5")
    print(get_contestants(html, "7343"))
