import os
import json
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import typer
from questionnaire import Questionnaire, Question, Category

# Load environment variables
load_dotenv()

# Initialize Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')

# Initialize console for rich output
console = Console()

class QuestionnaireChatbot:
    def __init__(self):
        self.questionnaire = Questionnaire()
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = """
You are a warm, empathetic mental health chatbot. Your goal is to gently gather information for a well-being assessment through natural conversation.
- Never repeat yourself verbatim.
- If the user is brief, non-specific, or repeats themselves, naturally shift the conversation to a new topic (appearance, energy, stress, etc.) using your own words.
- Use the conversation history and the list of topics you still need to cover, but never show the user a list or make it feel like a survey.
- Always keep the conversation flowing and supportive.
- Avoid sounding scripted or robotic; be creative and human-like in your responses.
- If the user seems uncomfortable, gently change the topic or offer reassurance.
"""
        self.last_pursued_question_ids: Optional[List[int]] = None
        self.pending_followup: Optional[str] = None
        self.followup_attempts: Dict[int, int] = {}

    def _get_relevant_questions(self, user_input: str) -> List[Tuple[Question, float]]:
        """Analyze user input to find relevant questions and their relevance scores."""
        relevant_questions = []
        
        # Convert input to lowercase for matching
        input_lower = user_input.lower()
        
        for question in self.questionnaire.get_unanswered_questions():
            # Check keywords
            keyword_matches = sum(1 for keyword in question.keywords if keyword.lower() in input_lower)
            # Check context hints
            context_matches = sum(1 for hint in question.context_hints if hint.lower() in input_lower)
            
            # Calculate relevance score (weighted sum of matches)
            relevance = (keyword_matches * 0.7) + (context_matches * 0.3)
            
            if relevance > 0:
                relevant_questions.append((question, relevance))
        
        # Sort by relevance score
        return sorted(relevant_questions, key=lambda x: x[1], reverse=True)

    def _analyze_response(self, user_input: str, relevant_questions: List[Tuple[Question, float]]) -> Optional[str]:
        """Analyze user response to determine if it matches any questionnaire options."""
        if not relevant_questions:
            return None
            
        # Get the most relevant question
        question, _ = relevant_questions[0]
        
        # Create a prompt for Gemini to analyze the response
        analysis_prompt = f"""Given this user response: "{user_input}"

Analyze it against these options for the question: "{question.text}"

Options:
{json.dumps(question.options, indent=2)}

Return ONLY the letter (A, B, C, or D) that best matches the user's response, or 'None' if no clear match.
Consider the context and implications of their words carefully."""

        try:
            response = model.generate_content(analysis_prompt)
            answer = response.text.strip().upper()
            
            # Validate the answer
            if answer in ['A', 'B', 'C', 'D']:
                return answer
        except Exception as e:
            console.print(f"[red]Error analyzing response: {e}[/red]")
        
        return None

    def analyze_single_question(self, user_input: str, question) -> Optional[str]:
        """
        Analyze the user input against a single question and return the answer letter if found.
        """
        conversation_context = json.dumps(self.conversation_history[-6:])
        analysis_prompt = f"""
Here is the recent conversation:
{conversation_context}

For the following question:
"{question.text}"
Options: {json.dumps(question.options)}

Only return an answer if the user's response is specific and provides enough detail to confidently select one option. If the response is vague, partial, or ambiguous, return None and do not infer an answer. If you return None, the bot will follow up for more detail.
If the user's most recent reply clearly answers this question (based on the conversation context), return the best matching option letter (A, B, C, or D). If not, return None. Do NOT infer an answer from generic or unrelated statements.
"""
        try:
            response = model.generate_content(analysis_prompt)
            answer = response.text.strip().upper()
            if answer in ['A', 'B', 'C', 'D']:
                return answer
        except Exception as e:
            console.print(f"[red]Error analyzing single question: {e}[/red]")
        return None

    def analyze_all_unanswered(self, user_input: str) -> dict:
        """
        Analyze the conversation context against all unanswered questions and return a dict of question_id: answer.
        """
        results = {}
        unanswered = self.questionnaire.get_unanswered_questions()
        if not unanswered:
            return results
        conversation_context = json.dumps(self.conversation_history[-6:])
        questions_block = '\n'.join([
            f"Q{q.id}: {q.text}\nOptions: {json.dumps(q.options)}" for q in unanswered
        ])
        prompt = f"""
Here is the recent conversation:
{conversation_context}

For each of these questions, only return an answer if the user's response is specific and provides enough detail to confidently select one option. If the response is vague, partial, or ambiguous, return None and do not infer an answer. If you return None, the bot will follow up for more detail.
If the user's most recent reply clearly answers the question (based on the conversation context), return the question number and the best matching option letter (A, B, C, or D). If not, return None for that question. Do NOT infer an answer from generic or unrelated statements.

Questions:
{questions_block}

Return your answer as a JSON object mapping question numbers to option letters or null. Example: {{"1": "A", "2": null, ...}}
"""
        try:
            response = model.generate_content(prompt)
            import json as _json
            text = response.text.strip()
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                text = match.group(0)
            answers = _json.loads(text)
            return {int(k): v for k, v in answers.items() if v and v in ['A','B','C','D']}
        except Exception as e:
            console.print(f"[red]Error in analyze_all_unanswered: {e}[/red]")
            return {}

    def get_next_unanswered_question(self) -> Optional[Question]:
        """Return the next unanswered question, or None if all are answered."""
        unanswered = self.questionnaire.get_unanswered_questions()
        return unanswered[0] if unanswered else None

    def generate_followup(self, question, context, user_reply):
        """
        Use Gemini to generate a dynamic, empathetic, context-aware follow-up prompt for a vague/insufficient answer.
        """
        followup_count = self.followup_attempts.get(question.id, 0)
        prompt = f"""
You are a warm, empathetic mental health chatbot. The user gave a vague or partial answer to this question:
"{question.text}"

Here is the recent conversation:
{json.dumps(context)}

The user's last reply was: "{user_reply}"

Generate a natural, empathetic follow-up question that gently asks for more detail, using the user's own words if possible. Vary your style based on how many times you've already followed up:
- First follow-up: be encouraging and curious, e.g., "Could you share a bit more about..."
- Second follow-up: be more specific or offer examples, e.g., "Would you say it happens most days, or just occasionally?"
- Third or more: acknowledge if the user doesn't want to answer, offer to skip, or gently move on.
Always start with a brief empathetic statement or reflection.
If the user seems uncomfortable, offer to skip the question (e.g., "If you'd rather not answer, that's completely okay.")
Return ONLY the follow-up message.
"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            console.print(f"[red]Error generating follow-up: {e}[/red]")
            return "Could you share a bit more about that? (If you'd rather not answer, that's okay.)"

    def generate_multi_question_prompt(self, questions):
        """
        Use Gemini to generate a single, natural prompt that covers multiple questionnaire items.
        """
        questions_text = '\n'.join([f"{i+1}. {q.text}" for i, q in enumerate(questions)])
        prompt = f"""
You are a warm, conversational mental health chatbot. Here are several questions I want to ask the user:
{questions_text}

Please combine these into a single, natural, conversational question or prompt that would help the user answer as many as possible at once. Make it sound friendly and supportive, not like a survey.
Return ONLY the combined prompt.
"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            console.print(f"[red]Error generating multi-question prompt: {e}[/red]")
            return "Could you tell me a bit about how you've been feeling in general lately?"

    def get_next_unanswered_group(self):
        """
        Return a list of unanswered questions from the same category (up to 3), or just the next unanswered question if none can be grouped.
        """
        unanswered = self.questionnaire.get_unanswered_questions()
        if not unanswered:
            return []
        # Group by category
        from collections import defaultdict
        cat_map = defaultdict(list)
        for q in unanswered:
            cat_map[q.category].append(q)
        # Find the largest group (with at least 2 questions), else fallback to single
        best_group = max(cat_map.values(), key=lambda l: len(l))
        if len(best_group) > 1:
            return best_group[:3]  # Limit to 3 for naturalness
        return [unanswered[0]]

    def process_user_reply(self, user_input: str) -> dict:
        """
        Processes user input to answer questions.
        1. Adds user message to history.
        2. Checks if the input answers the currently pursued questions.
        3. If not, or if no questions were pursued, checks against all unanswered questions.
        4. Sets up a follow-up prompt if the user's reply was vague on a pursued topic.
        """
        self.conversation_history.append({"role": "user", "content": user_input})
        answered_qids = {}

        # First, check if the user's reply answers the questions we are currently pursuing
        if self.last_pursued_question_ids:
            pursued_questions = [q for q in self.questionnaire.questions if q.id in self.last_pursued_question_ids]
            any_answered_in_group = False
            for question in pursued_questions:
                # Only check if it hasn't been answered yet in this turn
                if self.questionnaire.current_answers[question.id] is None:
                    answer = self.analyze_single_question(user_input, question)
                    if answer:
                        answered_qids[question.id] = answer
                        self.followup_attempts[question.id] = 0  # Reset on success
                        any_answered_in_group = True
                    # If this is the first unanswered question in the pursued group and we don't have an answer, set up a follow-up
                    elif not self.pending_followup:
                        self.followup_attempts[question.id] = self.followup_attempts.get(question.id, 0) + 1
                        self.pending_followup = self.generate_followup(question, self.conversation_history[-6:], user_input)
            
            # If we answered something, we can consider this line of inquiry complete for now
            if any_answered_in_group:
                self.last_pursued_question_ids = None
                self.pending_followup = None # Clear follow-up since we got an answer

        # If we weren't pursuing a topic, or the user's reply didn't answer it, check all questions opportunistically
        if not answered_qids:
            self.pending_followup = None  # User changed topic, so clear any pending follow-up
            all_unanswered_analysis = self.analyze_all_unanswered(user_input)
            for qid, ans in all_unanswered_analysis.items():
                answered_qids[qid] = ans

        return answered_qids

    def get_next_prompt(self, group: List[Question]):
        """
        Generate a short, conversational prompt for a group of questions, including conversation context.
        """
        conversation_context = self.conversation_history[-6:]
        prompt = f"""
You are a warm, conversational mental health chatbot. Your primary goal is to listen, understand, and make the user feel heard.

Here is the recent conversation:
{json.dumps(conversation_context)}

Be empapthetic in your response, and consider the message history. If appropriate, gently transition to a new, related line of inquiry based on these topics you want to learn about:
{chr(10).join([q.text for q in group])}

Combine the reflection and the next question into a single, natural, and supportive message. Do NOT list the questions. Use simple, everyday language. Do not sound robotic.
Return ONLY the message.
"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "Could you tell me a bit about how you've been feeling and your daily routine?"

    def _generate_response(self, user_input: str, relevant_questions: List[Tuple[Question, float]]) -> str:
        """
        Generates the next message from the chatbot.
        1. If a follow-up is pending, use it.
        2. Otherwise, get the next group of questions and generate a new, simple prompt.
        3. If all questions are answered, give a closing message.
        """
        # If a follow-up for a vague answer is pending, use that.
        if self.pending_followup:
            response = self.pending_followup
            self.pending_followup = None  # Consume the follow-up
        else:
            # Otherwise, get the next group of unanswered questions to talk about.
            next_group = self.get_next_unanswered_group()
            if not next_group:
                response = "Thank you for sharing all of this with me! Your assessment is complete. You can view the full report in the 'Questionnaire' tab now."
            else:
                self.last_pursued_question_ids = [q.id for q in next_group]
                response = self.get_next_prompt(next_group)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def chat(self):
        """Main chat loop."""
        console.print(Panel.fit(
            Markdown("# Mental Health Support Chat\n\nI'm here to chat and support you. How are you doing today?"),
            style="bold blue"
        ))
        
        while True:
            try:
                # Get user input
                user_input = typer.prompt("You")
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    break
                
                # Add user input to conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                
                # Find relevant questions
                relevant_questions = self._get_relevant_questions(user_input)
                
                # Analyze response for questionnaire answers
                if relevant_questions:
                    answer = self._analyze_response(user_input, relevant_questions)
                    if answer:
                        question, _ = relevant_questions[0]
                        self.questionnaire.current_answers[question.id] = answer
                
                # Generate and display response
                response = self._generate_response(user_input, relevant_questions)
                self.conversation_history.append({"role": "assistant", "content": response})
                
                console.print(Panel.fit(
                    Markdown(response),
                    style="bold green"
                ))
                
                # Check if all questions are answered
                if self.questionnaire.get_completion_percentage() == 100:
                    console.print("\n[bold yellow]Assessment complete! Thank you for chatting with me.[/bold yellow]")
                    self._display_results()
                    break
                
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Chat ended. Thank you for your time![/bold yellow]")
                break
            except Exception as e:
                console.print(f"[red]An error occurred: {e}[/red]")
                continue

    def _display_results(self):
        """Display the assessment results."""
        console.print("\n[bold]Assessment Results:[/bold]")
        
        for category in Category:
            score = self.questionnaire.get_category_score(category)
            console.print(f"\n{category.value}: {score:.1f}/4.0")
            
            # Get questions and answers for this category
            category_questions = [q for q in self.questionnaire.questions if q.category == category]
            for q in category_questions:
                answer = self.questionnaire.current_answers[q.id]
                if answer:
                    console.print(f"  • {q.text}")
                    console.print(f"    Answer: {answer} - {q.options[answer]}")

def main():
    """Main entry point."""
    if not os.getenv("GOOGLE_API_KEY"):
        console.print("[red]Error: GOOGLE_API_KEY environment variable not set.[/red]")
        console.print("Please create a .env file with your Google API key:")
        console.print("GOOGLE_API_KEY=your_api_key_here")
        return
    
    chatbot = QuestionnaireChatbot()
    chatbot.chat()

if __name__ == "__main__":
    typer.run(main) 