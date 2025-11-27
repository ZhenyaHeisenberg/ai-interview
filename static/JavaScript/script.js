// static/js/script.js
class InterviewAPI {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
    }

    async makeRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw new Error(`Cannot connect to server: ${error.message}`);
        }
    }

    async startInterview() {
        return await this.makeRequest('/start_interview', {
            method: 'POST'
        });
    }

    async getNextQuestion() {
        return await this.makeRequest('/next_question', {
            method: 'POST'
        });
    }

    async submitAnswer(answer) {
        return await this.makeRequest('/submit_answer', {
            method: 'POST',
            body: JSON.stringify({ answer })
        });
    }

    async submitCode(code) {
        return await this.makeRequest('/submit_code', {
            method: 'POST',
            body: JSON.stringify({ code })
        });
    }

    async getStatus() {
        return await this.makeRequest('/status');
    }
}

class InterviewApp {
    constructor() {
        this.api = new InterviewAPI();
        this.currentQuestion = null;
        this.currentTask = null;
        this.currentQuestionType = null;
        this.totalScore = 0;
        this.userLevel = "Junior";
        this.CNT_QUESTION = 3;
        this.CNT_CODES = 2;
        
        this.initializeApp();
    }

    async initializeApp() {
        this.setupEventListeners();
        this.updateTime();
        
        // Инициализация CodeMirror
        this.codeEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
            mode: 'python',
            theme: 'monokai',
            lineNumbers: true,
            indentUnit: 4,
            smartIndent: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            lineWrapping: true,
            readOnly: true
        });
        
        // Проверка соединения с сервером
        await this.checkServerConnection();
    }

    setupEventListeners() {
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendAnswer();
        });

        document.getElementById('user-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendAnswer();
            }
        });

        document.getElementById('submit-btn').addEventListener('click', () => {
            this.submitCode();
        });

        document.getElementById('run-btn').addEventListener('click', () => {
            this.runCode();
        });
    }

    async checkServerConnection() {
        try {
            this.addMessage("System", "Checking server connection...", "ai", true);
            
            const status = await this.api.getStatus();
            
            this.removeLastLoadingMessage();
            this.addMessage("System", "✅ Server connection established", "ai");
            
            // Start interview after successful connection check
            setTimeout(() => {
                this.startInterview();
            }, 1000);
            
        } catch (error) {
            this.removeLastLoadingMessage();
            this.addMessage("System", 
                `❌ Connection error: ${error.message}<br>
                 Please ensure:<br>
                 • Server is running on localhost:5000<br>
                 • You executed: python app.py<br>
                 • Browser can access localhost`, 
                "ai");
            
            // Show retry button
            const retryButton = document.createElement('button');
            retryButton.textContent = 'Retry Connection';
            retryButton.className = 'retry-btn';
            retryButton.onclick = () => this.checkServerConnection();
            
            const messageDiv = this.addMessage("System", "", "ai");
            messageDiv.querySelector('.message-content').appendChild(retryButton);
        }
    }

    async startInterview() {
        try {
            this.addMessage("AI Interviewer", "Starting interview...", "ai", true);
            
            const response = await this.api.startInterview();
            
            this.removeLastLoadingMessage();
            
            this.userLevel = response.user_level;
            this.CNT_QUESTION = response.config.questions_count;
            this.CNT_CODES = response.config.codes_count;
            
            document.getElementById('user-level').textContent = this.userLevel;
            
            this.addMessage("AI Interviewer", 
                `Welcome to the interview!<br>
                 Your initial level: <strong>${this.userLevel}</strong><br>
                 You will be asked: <strong>${this.CNT_QUESTION} questions</strong> and <strong>${this.CNT_CODES} programming tasks</strong><br>
                 Let's get started!`, 
                "ai");
            
            this.generateQuestionIndicators();
            await this.nextQuestion();
            
        } catch (error) {
            this.removeLastLoadingMessage();
            this.addMessage("AI Interviewer", 
                `Error starting interview: ${error.message}`, 
                "ai");
        }
    }

    generateQuestionIndicators() {
        const questionsList = document.getElementById('questions-list');
        questionsList.innerHTML = '';
        
        for (let i = 1; i <= this.CNT_QUESTION; i++) {
            const indicator = document.createElement('div');
            indicator.className = 'question-indicator text-task';
            indicator.textContent = i;
            questionsList.appendChild(indicator);
        }
        
        for (let i = 1; i <= this.CNT_CODES; i++) {
            const indicator = document.createElement('div');
            indicator.className = 'question-indicator code-task';
            indicator.textContent = this.CNT_QUESTION + i;
            questionsList.appendChild(indicator);
        }
        
        document.getElementById('questions-count').textContent = 
            `${this.CNT_QUESTION}/${this.CNT_CODES}`;
    }

    async nextQuestion() {
        try {
            this.addMessage("AI Interviewer", "Preparing next question...", "ai", true);
            
            const response = await this.api.getNextQuestion();
            
            this.removeLastLoadingMessage();
            
            if (response.completed) {
                this.completeInterview(response);
                return;
            }
            
            if (response.type === 'text') {
                this.currentQuestionType = 'text';
                this.currentQuestion = response.question;
                
                this.addMessage("AI Interviewer", 
                    `Topic: <strong>${response.topic}</strong><br>
                     Difficulty: <strong>${response.difficulty}</strong><br><br>
                     ${response.question}`, 
                    "ai");
                
                document.getElementById('user-input').disabled = false;
                document.getElementById('send-btn').disabled = false;
                document.getElementById('user-input').focus();
                
            } else if (response.type === 'code') {
                this.currentQuestionType = 'code';
                this.currentTask = response.task;
                
                this.addMessage("AI Interviewer", 
                    `Topic: <strong>${response.topic}</strong><br>
                     Difficulty: <strong>${response.difficulty}</strong><br><br>
                     ${response.task}`, 
                    "ai");
                
                this.codeEditor.setValue("# Write your solution here\n\n");
                this.codeEditor.setOption('readOnly', false);
                document.getElementById('run-btn').disabled = false;
                document.getElementById('submit-btn').disabled = false;
            }
            
            this.updateProgress(response.progress);
            
        } catch (error) {
            this.removeLastLoadingMessage();
            this.addMessage("AI Interviewer", 
                `Error getting question: ${error.message}`, 
                "ai");
        }
    }

    async sendAnswer() {
        const userInput = document.getElementById('user-input');
        const answer = userInput.value.trim();
        
        if (!answer) {
            return;
        }
        
        this.addMessage("You", answer, "user");
        userInput.value = '';
        userInput.disabled = true;
        document.getElementById('send-btn').disabled = true;
        
        this.addMessage("AI Interviewer", "Evaluating your answer...", "ai", true);
        
        try {
            const response = await this.api.submitAnswer(answer);
            
            this.removeLastLoadingMessage();
            
            this.addMessage("AI Interviewer", 
                `Score: <span class="score">${response.score}/10</span><br>${response.explanation}`, 
                "ai");
            
            this.addMessage("AI Interviewer", 
                `<strong>Feedback:</strong><br>${response.feedback}`, 
                "ai");
            
            this.totalScore = response.total_score;
            this.userLevel = response.user_level;
            
            document.getElementById('total-score').textContent = this.totalScore;
            document.getElementById('user-level').textContent = this.userLevel;
            
            setTimeout(() => {
                this.nextQuestion();
            }, 2000);
            
        } catch (error) {
            this.removeLastLoadingMessage();
            this.addMessage("AI Interviewer", 
                `Error evaluating answer: ${error.message}`, 
                "ai");
            
            userInput.disabled = false;
            document.getElementById('send-btn').disabled = false;
        }
    }

    async submitCode() {
        const code = this.codeEditor.getValue();
        
        this.addMessage("You", `<pre><code>${code}</code></pre>`, "user");
        
        document.getElementById('run-btn').disabled = true;
        document.getElementById('submit-btn').disabled = true;
        this.codeEditor.setOption('readOnly', true);
        
        this.addMessage("AI Interviewer", "Evaluating your solution...", "ai", true);
        
        try {
            const response = await this.api.submitCode(code);
            
            this.removeLastLoadingMessage();
            
            this.addMessage("AI Interviewer", 
                `Code score: <span class="score">${response.score}/20</span>`, 
                "ai");
            
            this.addMessage("AI Interviewer", 
                `<div class="feedback">${response.detailed_feedback}</div>`, 
                "ai");
            
            this.addMessage("AI Interviewer", 
                `<strong>Additional feedback:</strong><br>${response.additional_feedback}`, 
                "ai");
            
            this.totalScore = response.total_score;
            this.userLevel = response.user_level;
            
            document.getElementById('total-score').textContent = this.totalScore;
            document.getElementById('user-level').textContent = this.userLevel;
            
            setTimeout(() => {
                this.nextQuestion();
            }, 3000);
            
        } catch (error) {
            this.removeLastLoadingMessage();
            this.addMessage("AI Interviewer", 
                `Error evaluating code: ${error.message}`, 
                "ai");
            
            document.getElementById('run-btn').disabled = false;
            document.getElementById('submit-btn').disabled = false;
            this.codeEditor.setOption('readOnly', false);
        }
    }

    runCode() {
        const code = this.codeEditor.getValue();
        this.addMessage("You", `<pre><code>${code}</code></pre>`, "user");
        
        this.addMessage("AI Interviewer", 
            "Running code... (Execution simulated in demo)", 
            "ai");
    }

    updateProgress(progress) {
        const totalTasks = this.CNT_QUESTION + this.CNT_CODES;
        const completedTasks = (progress.current_question - 1) + progress.current_code;
        const progressPercentage = (completedTasks / totalTasks) * 100;
        
        document.getElementById('progress-fill').style.width = `${progressPercentage}%`;
        document.getElementById('completed').textContent = `${completedTasks}/${totalTasks}`;
    }

    completeInterview(response) {
        const percentage = Math.round((response.total_score / response.max_score) * 100);
        
        this.addMessage("AI Interviewer", 
            `<div class="interview-completed">
                <h3>Interview Completed!</h3>
                <p>Your final result: <strong>${response.total_score}/${response.max_score} (${percentage}%)</strong></p>
                <p>Your final level: <strong>${response.user_level}</strong></p>
                <p>Thank you for participating!</p>
            </div>`, 
            "ai");
        
        document.getElementById('user-input').disabled = true;
        document.getElementById('send-btn').disabled = true;
        document.getElementById('run-btn').disabled = true;
        document.getElementById('submit-btn').disabled = true;
        this.codeEditor.setOption('readOnly', true);
    }

    updateTime() {
        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');
        document.getElementById('current-time').textContent = timeString;
    }

    addMessage(sender, content, type, isLoading = false) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const currentTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span>${sender}</span>
                <span>${currentTime}</span>
            </div>
            <div class="message-content">
                ${isLoading ? '<div class="loading"></div>' : content}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }

    removeLastLoadingMessage() {
        const chatMessages = document.getElementById('chat-messages');
        const messages = chatMessages.querySelectorAll('.message');
        
        for (let i = messages.length - 1; i >= 0; i--) {
            const message = messages[i];
            const loadingElement = message.querySelector('.loading');
            if (loadingElement) {
                message.remove();
                break;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.interviewApp = new InterviewApp();
});