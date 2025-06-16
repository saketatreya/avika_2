import os
import json
import streamlit as st
import google.generativeai as genai
from chatbot import QuestionnaireChatbot, Category
import time
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
from streamlit_chat import message

# Configure the Gemini API key from Streamlit Secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    if not api_key:
        st.error("🛑 GOOGLE_API_KEY secret is not set. Please add it to your Streamlit Cloud app secrets.")
        st.stop()
    genai.configure(api_key=api_key)
except KeyError:
    st.error("🛑 GOOGLE_API_KEY secret not found. Please add it to your Streamlit Cloud app secrets.")
    st.stop()

# Load environment variables
# load_dotenv() - This is no longer needed for cloud deployment
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = QuestionnaireChatbot()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_dev_tools' not in st.session_state:
    st.session_state.show_dev_tools = False
if 'show_raw_output' not in st.session_state:
    st.session_state.show_raw_output = False
if 'show_conversation' not in st.session_state:
    st.session_state.show_conversation = False
if 'debug_log' not in st.session_state:
    st.session_state.debug_log = []
if 'pending_simulated_message' not in st.session_state:
    st.session_state.pending_simulated_message = None
if 'sim_type_to_generate' not in st.session_state:
    st.session_state.sim_type_to_generate = None
if 'generating_sim' not in st.session_state:
    st.session_state.generating_sim = False

def log_debug(message: str):
    """Add a debug message to the log with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.debug_log.append(f"[{timestamp}] {message}")

def simulate_response(state: str) -> str:
    """Simulate a user response using Gemini."""
    conversation_context = st.session_state.chatbot.conversation_history[-6:]
    prompt = f"""
You are simulating a user in a mental health chatbot conversation. Here is the recent conversation:
{json.dumps(conversation_context)}

Generate a single user message that is:
- GENERIC: if state is 'generic', make it vague, non-committal, or brief (e.g., 'I'm fine', 'not much', 'okay').
- DETAILED: if state is 'detailed', make it specific, descriptive, and relevant to the last bot question.
- CONTRADICTORY: if state is 'contradictory', make it self-contradictory or ambiguous (e.g., 'I'm great, but also exhausted').

State: {state.upper()}

Return ONLY the user message, nothing else."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        log_debug(f"Error in simulate_response: {e}")
        return "I'm not sure how to respond to that."

def display_results():
    """Display assessment results with visualizations."""
    results = {}
    for category in Category:
        score = st.session_state.chatbot.questionnaire.get_category_score(category)
        category_questions = [
            {
                'question': q.text,
                'answer': st.session_state.chatbot.questionnaire.current_answers[q.id]['answer'],
                'option': q.options[st.session_state.chatbot.questionnaire.current_answers[q.id]['answer']]
            }
            for q in st.session_state.chatbot.questionnaire.questions
            if q.category == category and st.session_state.chatbot.questionnaire.current_answers[q.id]
        ]
        results[category.value] = {
            'score': score,
            'questions': category_questions
        }
    
    # Create radar chart data
    categories = list(results.keys())
    scores = [results[cat]['score'] for cat in categories]
    
    # Create radar chart
    fig = px.line_polar(
        r=scores,
        theta=categories,
        line_close=True,
        range_r=[0, 4],
        title="Assessment Results by Category"
    )
    fig.update_traces(fill='toself')
    st.plotly_chart(fig)
    
    # Display detailed results
    for category, data in results.items():
        with st.expander(f"{category} (Score: {data['score']:.1f})"):
            for q in data['questions']:
                st.write(f"**Q:** {q['question']}")
                st.write(f"**A:** {q['option']}")

def display_category_details(category: Category):
    """Display detailed questionnaire view for a category."""
    st.subheader(f"{category.value} Questions")
    
    # Get questions and answers for this category
    category_questions = [q for q in st.session_state.chatbot.questionnaire.questions if q.category == category]
    
    # Create a DataFrame for better display
    data = []
    for q in category_questions:
        answer = st.session_state.chatbot.questionnaire.current_answers[q.id]
        data.append({
            'Question': q.text,
            'Status': '✅ Answered' if answer else '⏳ Pending',
            'Answer': q.options[answer] if answer else 'Not answered yet',
            'Keywords': ', '.join(q.keywords),
            'Context Hints': ', '.join(q.context_hints)
        })
    
    df = pd.DataFrame(data)
    
    # Display with custom styling
    st.dataframe(
        df,
        column_config={
            'Question': st.column_config.TextColumn('Question', width='large'),
            'Status': st.column_config.TextColumn('Status', width='small'),
            'Answer': st.column_config.TextColumn('Answer', width='medium'),
            'Keywords': st.column_config.TextColumn('Keywords', width='medium'),
            'Context Hints': st.column_config.TextColumn('Context Hints', width='medium')
        },
        hide_index=True,
        use_container_width=True
    )

def show_thinking_indicator():
    """Show an animated thinking indicator."""
    st.markdown("""
        <div style='text-align:center; margin: 1rem 0;'>
            <span class='thinking-dot'></span>
            <span class='thinking-dot'></span>
            <span class='thinking-dot'></span>
            <span style='margin-left: 0.5rem; color: #aaa;'>Avika is thinking...</span>
        </div>
        <style>
        .thinking-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            margin: 0 2px;
            background: #4CAF50;
            border-radius: 50%;
            animation: thinking-bounce 1.2s infinite both;
        }
        .thinking-dot:nth-child(1) { animation-delay: 0s; }
        .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes thinking-bounce {
            0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
            40% { transform: scale(1.2); opacity: 1; }
        }
        </style>
    """, unsafe_allow_html=True)

def ensure_initial_avika_message():
    """Ensure the conversation starts with an initial Avika message."""
    if not st.session_state.messages:
        initial_msg = "Hi! I'm Avika. I'm here to chat about your well-being. Feel free to share as much or as little as you like—there's no pressure. How are you feeling today?"
        st.session_state.messages.append({"role": "assistant", "content": initial_msg})
        st.session_state.awaiting_first_user = True

def chat_message(role, content, key=None):
    """Display a chat message with custom formatting and alignment."""
    if role == "user":
        st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; margin-bottom: 1rem;'>
                <div style='background: #23272f; color: #fff; padding: 1rem 1.2rem; border-radius: 1.2rem 0 1.2rem 1.2rem; margin-left: 0.5rem; max-width: 70%; text-align: right;'>
                    <b style='color:#4CAF50;'>You</b><br>{content}
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style='display: flex; justify-content: flex-start; margin-bottom: 1rem;'>
                <div style='background: #2b313e; color: #fff; padding: 1rem 1.2rem; border-radius: 0 1.2rem 1.2rem 1.2rem; margin-right: 0.5rem; max-width: 70%; text-align: left;'>
                    <b style='color:#4CAF50;'>Avika</b><br>{content}
                </div>
            </div>
        """, unsafe_allow_html=True)

def debug_panel(debug_data):
    """Show a collapsible debug panel below the chat."""
    with st.expander("🛠️ Debug Info (click to expand)"):
        st.markdown("**Last Gemini Prompt:**")
        st.code(debug_data.get("prompt", ""), language="text")
        st.markdown("**Last Gemini Response:**")
        st.code(debug_data.get("response", ""), language="text")
        st.markdown("**Conversation Context:**")
        st.json(debug_data.get("context", []))
        if debug_data.get("error"):
            st.error(debug_data["error"])

def questionnaire_card(question, answer_data, on_select):
    """Display a single questionnaire item as a card, showing the source of the answer."""
    st.markdown(f"""
        <div style='background: #23272f; border-radius: 1rem; padding: 1.2rem 1.5rem; margin-bottom: 1.2rem; box-shadow: 0 2px 8px #0002;'>
            <div style='font-weight: 600; color: #fff; margin-bottom: 0.5rem;'>{question.text}</div>
    """, unsafe_allow_html=True)

    if answer_data:
        answer_source = "Avika's answer" if answer_data['source'] == 'avika' else "Your answer"
        answer_text = question.options[answer_data['answer']]
        st.markdown(f"<div style='color: #4CAF50; font-weight: 500; margin-bottom: 0.5rem;'>{answer_source}: {answer_text}</div>", unsafe_allow_html=True)
    else:
        # User can select an answer
        user_choice = st.radio(
            "Select your answer:",
            options=list(question.options.keys()),
            format_func=lambda k: f"{k}: {question.options[k]}",
            key=f"q_{question.id}_radio",
            label_visibility="collapsed"
        )
        if st.button("Save Answer", key=f"q_{question.id}_save"):
            on_select(user_choice)
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

def show_questionnaire():
    st.header("Assessment Progress")
    progress = st.session_state.chatbot.questionnaire.get_completion_percentage()
    st.progress(progress / 100)
    st.write(f"Overall Progress: {progress:.1f}%")
    
    category_tabs = st.tabs([cat.value for cat in Category])
    
    all_questions = st.session_state.chatbot.questionnaire.questions
    all_answers = st.session_state.chatbot.questionnaire.current_answers
    
    is_complete = all(all_answers.values())

    for i, category in enumerate(Category):
        with category_tabs[i]:
            st.subheader(f"{category.value} Questions")
            category_questions = [q for q in all_questions if q.category == category]
            for q in category_questions:
                answer_data = all_answers.get(q.id)
                
                def create_on_select(question_id):
                    def on_select_callback(selected_answer):
                        st.session_state.chatbot.questionnaire.current_answers[question_id] = {
                            'answer': selected_answer,
                            'source': 'user'
                        }
                    return on_select_callback

                questionnaire_card(q, answer_data, on_select=create_on_select(q.id))

    if is_complete:
        st.success("All questions answered! You can now view your report.")
        if st.button("View Report"):
            st.session_state.show_report = True
            
    if st.session_state.get("show_report"):
        st.header("Assessment Report")
        display_results()

def handle_user_message(user_message: str):
    """
    Appends a user message to the chat, gets a bot response, and updates state.
    """
    if not user_message:
        return

    st.session_state.messages.append({"role": "user", "content": user_message})
    log_debug(f"User message: {user_message}")
    
    thinking_placeholder = st.empty()
    with thinking_placeholder.container():
        show_thinking_indicator()
    
    try:
        # Process the user's reply to fill in the questionnaire
        answers = st.session_state.chatbot.process_user_reply(user_message)
        for qid, answer in answers.items():
            st.session_state.chatbot.questionnaire.current_answers[qid] = {'answer': answer, 'source': 'avika'}
        
        # Now, generate a context-aware response using the full conversation history
        response = st.session_state.chatbot._generate_response(user_message, [])
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    except Exception as e:
        error_message = f"I'm having trouble connecting to the AI service right now. Please check if the API key is configured correctly in your Streamlit secrets. \n\n**Details:** {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    finally:
        # Always clean up and rerun
        thinking_placeholder.empty()
        st.session_state.pending_simulated_message = None
        st.session_state.sim_type_to_generate = None
        st.rerun()

def main():
    st.set_page_config(
        page_title="Avika - Mental Health Assessment",
        page_icon="🧠",
        layout="wide"
    )
    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
            padding-left: 1.2rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            white-space: pre-wrap;
            background-color: #262730;
            border-radius: 4px 4px 0 0;
            gap: 1rem;
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
            font-size: 1.1rem;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4CAF50;
        }
        .sim-btn-row {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }
        .sim-btn-row button {
            background: #23272f;
            color: #fff;
            border: none;
            border-radius: 0.5rem;
            padding: 0.6rem 1.2rem;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .sim-btn-row button:hover {
            background: #4CAF50;
            color: #fff;
        }
        </style>
    """, unsafe_allow_html=True)
    st.title("🧠 Avika - Mental Health Assessment")
    st.markdown("""
        Welcome! I'm here to have a natural conversation about your well-being.
        I'll ask about different aspects of your life, but we'll keep it casual and supportive.
    """)
    tab1, tab2 = st.tabs(["💬 Chat", "📋 Questionnaire"])
    with tab1:
        ensure_initial_avika_message()
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.messages):
                chat_message(msg["role"], msg["content"], key=f"msg_{i}")

        # Display pending simulation and get user action
        if st.session_state.pending_simulated_message:
            pending_msg = st.session_state.pending_simulated_message
            st.info(f"**Suggested response:** \"{pending_msg}\"")
            c1, c2, _ = st.columns([1, 1, 5])
            if c1.button("✅ Send", key="send_sim"):
                handle_user_message(pending_msg)
            if c2.button("❌ Discard", key="discard_sim"):
                st.session_state.pending_simulated_message = None
                st.rerun()

        sim_in_progress = bool(st.session_state.get('sim_type_to_generate'))
        user_input = st.chat_input("Type your message here...", key="chat_input", disabled=sim_in_progress)
        if user_input:
            handle_user_message(user_input)

        # Simulation buttons below chat input
        st.markdown("<div class='sim-btn-row'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        def set_sim_type(sim_type):
            st.session_state.sim_type_to_generate = sim_type

        col1.button("🎲 Generic", on_click=set_sim_type, args=("generic",), disabled=sim_in_progress)
        col2.button("📝 Detailed", on_click=set_sim_type, args=("detailed",), disabled=sim_in_progress)
        col3.button("🤔 Contradictory", on_click=set_sim_type, args=("contradictory",), disabled=sim_in_progress)
        
        st.markdown("</div>", unsafe_allow_html=True)

        # Generation logic, runs on the rerun after a button is clicked
        if sim_in_progress:
            sim_type = st.session_state.sim_type_to_generate
            with st.spinner(f"Generating '{sim_type}' response..."):
                response = simulate_response(sim_type)
            st.session_state.pending_simulated_message = response
            st.session_state.sim_type_to_generate = None
            st.rerun()
            
        # JavaScript to auto-scroll the chat to the bottom
        st.components.v1.html(
            """
            <script>
                // Small delay to allow the message to render before scrolling
                setTimeout(function() {
                    var chatContainer = window.parent.document.querySelector('section.main');
                    chatContainer.scrollTo(0, chatContainer.scrollHeight);
                }, 150);
            </script>
            """,
            height=0
        )

    with tab2:
        show_questionnaire()

if __name__ == "__main__":
    main() 