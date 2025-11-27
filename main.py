import random

from src.level_system import UserLevelSystem
from src.settings import CNT_QUESTION, CNT_CODES, THEME, API_KEY
from src.interviewer import SciBoxHelper


def main():
    user_system = UserLevelSystem(CNT_QUESTION, CNT_CODES)
    sci_box = SciBoxHelper(API_KEY)

    for _ in range(CNT_QUESTION):
        topic = random.choice(THEME)
        print(sci_box.generate_question(topic, user_system.get_user_lvl()))
        user_system.update_user_lvl(10)

    print(user_system.get_user_lvl())

if __name__ == '__main__':
    main()