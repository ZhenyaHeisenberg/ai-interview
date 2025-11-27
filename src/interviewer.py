    # interviewer.py
import json
import re
from typing import Tuple

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available, using demo mode")

class SciBoxHelper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://llm.t1v.scibox.tech/v1"
            )
        else:
            self.client = None

    def _clean_response(self, text: str) -> str:
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        text = re.sub(r'\.\.\..*$', '', text)
        text = re.sub(r'\s+и т\.\s*д\.*.*$', '', text)
        text = re.sub(r',\s*$', '', text)
        text = re.sub(r'{\s*$', '', text)
        text = re.sub(r'\[\s*$', '', text)
        return text.strip()

    def _ensure_complete_sentence(self, text: str) -> str:
        if not text:
            return text

        if text[-1] in [',', ';', ':', '-']:
            text = text[:-1]

        if text and text[-1] not in ['.', '!', '?']:
            if not re.search(r'\d+$', text):
                text += '.'

        return text

    def generate_question(self, topic: str, difficulty_level: str, subject: str = "programming") -> str:
        if not self.client:
            return f"Демо вопрос по теме '{topic}' для уровня {difficulty_level}: Объясните основные принципы."

        prompt = f"""
        Сгенерируй ОДИН четкий вопрос по теме "{topic}" для уровня "{difficulty_level}".
        Верни ТОЛЬКО текст вопроса без дополнительных пояснений.
        Убедись, что вопрос полный и законченный.
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen3-32b-awq",
                messages=[
                    {"role": "system",
                     "content": "/no_think Ты генератор учебных вопросов. Возвращай только чистый текст вопроса."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            result = self._clean_response(response.choices[0].message.content.strip())
            return self._ensure_complete_sentence(result)
        except Exception as e:
            return f"Ошибка генерации вопроса: {str(e)}"

    def evaluate_answer(self, question: str, answer: str) -> Tuple[int, str]:
        if not self.client:
            return 7, "Демо оценка: ответ принят к рассмотрению"

        evaluation_prompt = f"""
        ВОПРОС: {question}
        ОТВЕТ: {answer}

        Оцени по шкале 0-10 баллов и верни ТОЛЬКО JSON:
        {{
            "score": число 0-10,
            "explanation": "пояснение"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen3-32b-awq",
                messages=[
                    {"role": "system", "content": "/no_think Ты оценщик. Возвращай только JSON."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                max_tokens=400
            )

            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation["score"], evaluation["explanation"]
            else:
                return 0, f"Не удалось распарсить JSON: {result_text}"

        except Exception as e:
            return 0, f"Ошибка оценки: {str(e)}"

    def generate_feedback(self, question: str, answer: str, score: int) -> str:
        if not self.client:
            return "Демо обратная связь: хорошая работа, продолжайте в том же духе!"

        feedback_prompt = f"""
        ВОПРОС: {question}
        ОТВЕТ: {answer}
        ОЦЕНКА: {score}/10

        Сгенерируй конструктивную обратную связь. Будь конкретным и полезным.
        Верни только текст обратной связи.
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen3-32b-awq",
                messages=[
                    {"role": "system", "content": "/no_think Ты преподаватель. Возвращай только обратную связь."},
                    {"role": "user", "content": feedback_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            result = self._clean_response(response.choices[0].message.content.strip())
            return self._ensure_complete_sentence(result)
        except Exception as e:
            return f"Ошибка генерации обратной связи: {str(e)}"

    def evaluate_code(self, programming_task: str, code: str, language: str = "Python") -> Tuple[int, str]:
        if not self.client:
            return 15, "Демо оценка кода: решение рабочее, хороший стиль программирования"

        code_evaluation_prompt = f"""
        ЗАДАЧА: {programming_task}
        КОД:
        ```{language}
        {code}
        ```

        Оцени код по шкале 0-20 и верни ТОЛЬКО JSON:
        {{
            "score": число 0-20,
            "analysis": "анализ",
            "suggestions": "предложения",
            "correctness": "корректность",
            "efficiency": "эффективность",
            "style": "стиль"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen3-coder-30b-a3b-instruct-fp8",
                messages=[
                    {"role": "system", "content": "Ты code review эксперт. Возвращай только JSON."},
                    {"role": "user", "content": code_evaluation_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )

            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())

                detailed_feedback = f"""
ОЦЕНКА: {evaluation['score']}/20
КОРРЕКТНОСТЬ: {evaluation['correctness']}
ЭФФЕКТИВНОСТЬ: {evaluation['efficiency']}
СТИЛЬ: {evaluation['style']}

АНАЛИЗ:
{evaluation['analysis']}

ПРЕДЛОЖЕНИЯ:
{evaluation['suggestions']}
"""
                return evaluation["score"], detailed_feedback.strip()
            else:
                return 0, f"Не удалось распарсить JSON: {result_text}"

        except Exception as e:
            return 0, f"Ошибка оценки кода: {str(e)}"

    def generate_coding_task(self, topic: str, difficulty_level: str, language: str = "Python") -> str:
        if not self.client:
            return f"Демо задание по теме '{topic}': Напишите функцию для работы со списками на {language}"

        prompt = f"""
        Сгенерируй ОДНО четкое задание на написание кода по теме "{topic}" 
        для уровня сложности "{difficulty_level}" на языке {language}.

        Требования:
        - Задание должно быть практическим и конкретным
        - Соответствовать уровню сложности
        - Содержать четкие требования
        - Быть самодостаточным

        Верни ТОЛЬКО текст задания без дополнительных пояснений.
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen3-coder-30b-a3b-instruct-fp8",
                messages=[
                    {"role": "system",
                     "content": "/no_think Ты генератор программистских заданий. Возвращай только текст задания."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            result = self._clean_response(response.choices[0].message.content.strip())
            return self._ensure_complete_sentence(result)
        except Exception as e:
            return f"Ошибка генерации задания: {str(e)}"

    def generate_code_feedback(self, programming_task: str, code: str, language: str = "Python") -> str:
        if not self.client:
            return "Демо обратная связь по коду: хороший стиль, решение рабочее"

        feedback_prompt = f"""
        ЗАДАЧА: {programming_task}
        КОД СТУДЕНТА:
        ```{language}
        {code}
        ```

        Сгенерируй конструктивную обратную связь по коду. Сосредоточься на:
        1. Что сделано правильно и хорошо
        2. Какие есть ошибки или проблемы
        3. Конкретные рекомендации по улучшению

        Будь конкретным, доброжелательным и мотивирующим.
        Верни только текст обратной связи без оценки в баллах.
        """

        try:
            response = self.client.chat.completions.create(
                model="qwen3-coder-30b-a3b-instruct-fp8",
                messages=[
                    {"role": "system",
                     "content": "/no_think Ты ментор по программированию. Возвращай только обратную связь."},
                    {"role": "user", "content": feedback_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            result = self._clean_response(response.choices[0].message.content.strip())
            return self._ensure_complete_sentence(result)
        except Exception as e:
            return f"Ошибка генерации обратной связи: {str(e)}"
        

# src/interviewer.py - обновите метод evaluate_code
def evaluate_code(self, programming_task: str, code: str, language: str = "Python") -> Tuple[int, str]:
    # Проверка на пустой код
    if not code or code.strip() == "" or code.strip() == "# Напишите ваше решение здесь":
        return 0, """
ОЦЕНКА: 0/20
КОРРЕКТНОСТЬ: Не представлено решение
ЭФФЕКТИВНОСТЬ: Не применимо
СТИЛЬ: Не применимо

АНАЛИЗ:
Код не предоставлен. Пожалуйста, напишите решение задачи.

ПРЕДЛОЖЕНИЯ:
Начните с анализа задачи и создания базовой структуры решения.
"""

    code_evaluation_prompt = f"""
    ЗАДАЧА: {programming_task}
    КОД:
    ```{language}
    {code}
    ```

    Оцени код по шкале 0-20 и верни ТОЛЬКО JSON:
    {{
        "score": число 0-20,
        "analysis": "детальный анализ решения",
        "suggestions": "конкретные предложения по улучшению",
        "correctness": "оценка корректности решения",
        "efficiency": "оценка эффективности алгоритма",
        "style": "оценка стиля кода и читаемости"
    }}

    Критерии оценки:
    - 0-5: код не работает или полностью не соответствует задаче
    - 6-10: код имеет серьезные ошибки, но есть попытка решения
    - 11-15: код работает, но есть недочеты в логике или стиле
    - 16-20: код корректно решает задачу, хороший стиль

    Будь строгим в оценке. Пустой или почти пустой код должен получать 0 баллов.
    """

    try:
        response = self.client.chat.completions.create(
            model="qwen3-coder-30b-a3b-instruct-fp8",
            messages=[
                {"role": "system", "content": "Ты строгий code review эксперт. Возвращай только JSON. Будь объективным в оценках."},
                {"role": "user", "content": code_evaluation_prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )

        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group())
            
            # Дополнительная проверка на минимальное качество кода
            actual_score = evaluation["score"]
            
            # Если код слишком короткий или пустой, понижаем оценку
            lines_of_code = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
            if lines_of_code < 2:
                actual_score = max(0, actual_score - 10)
            
            detailed_feedback = f"""
ОЦЕНКА: {actual_score}/20
КОРРЕКТНОСТЬ: {evaluation['correctness']}
ЭФФЕКТИВНОСТЬ: {evaluation['efficiency']}
СТИЛЬ: {evaluation['style']}

АНАЛИЗ:
{evaluation['analysis']}

ПРЕДЛОЖЕНИЯ:
{evaluation['suggestions']}
"""
            return actual_score, detailed_feedback.strip()
        else:
            return 0, f"Не удалось распарсить JSON: {result_text}"

    except Exception as e:
        return 0, f"Ошибка оценки кода: {str(e)}"