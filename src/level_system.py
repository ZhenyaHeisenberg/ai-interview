# level_system.py
class UserLevelSystem():
    def __init__(self, cnt_questions, cnt_codes):
        self.user_lvl = 1
        self.total_score = 0
        self.assessments_cnt = 0

        self.cnt_questions = cnt_questions
        self.cnt_codes = cnt_codes

        self.max_question_score = 10
        self.max_code_score = 20
        self.max_score = self.cnt_questions * self.max_question_score + self.cnt_codes * self.max_code_score

    def update_user_lvl(self, score):
        self.total_score += score
        self.assessments_cnt += 1

        percentage = (self.total_score / self.max_score) * 100

        if percentage >= 70 and self.user_lvl < 3:
            self.user_lvl += 1
        elif percentage <= 30 and self.user_lvl > 1:
            self.user_lvl -= 1

    def get_user_lvl(self):
        if self.user_lvl == 1:
            return "Junior"
        elif self.user_lvl == 2:
            return "Middle"
        else:
            return "Senior"