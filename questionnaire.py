from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class Category(Enum):
    APPEARANCE_AWARENESS = "Appearance & Awareness"
    ATTITUDE_ENGAGEMENT = "Attitude & Engagement"
    BEHAVIOR_PERFORMANCE = "Behavior and Performance"
    SOMATIC_COMPLAINTS = "Somatic Complaints"

@dataclass
class Question:
    id: int
    category: Category
    text: str
    options: Dict[str, str]
    keywords: List[str]  # Keywords to look for in conversation
    context_hints: List[str]  # Phrases that might indicate relevant context

@dataclass
class Questionnaire:
    questions: List[Question]
    current_answers: Dict[int, Optional[Dict[str, str]]]
    
    def __init__(self):
        self.questions = [
            # Appearance & Awareness
            Question(
                id=1,
                category=Category.APPEARANCE_AWARENESS,
                text="Over the past two weeks, how would you describe your physical appearance and grooming habits?",
                options={
                    "A": "Appropriate – Well-dressed and neatly groomed throughout",
                    "B": "Well-groomed – Generally clean and tidy, with some attention to appearance",
                    "C": "Disheveled – Often untidy or unkempt, but basic hygiene maintained",
                    "D": "Neglected hygiene – Frequently poorly groomed, with noticeable issues"
                },
                keywords=["appearance", "grooming", "dressed", "clean", "hygiene", "clothes", "shower", "shaved", "makeup"],
                context_hints=["how do you look", "how are you dressed", "how do you take care of yourself"]
            ),
            Question(
                id=2,
                category=Category.APPEARANCE_AWARENESS,
                text="Over the past two weeks, how connected have you felt to your surroundings?",
                options={
                    "A": "Fully connected – Actively engaged and aware of your environment",
                    "B": "Partially connected – Sometimes engaged, but with occasional feelings of detachment",
                    "C": "Disconnected – Frequently felt distant or detached from surroundings",
                    "D": "Completely detached – Felt removed or numb, as though observing rather than participating"
                },
                keywords=["connected", "surroundings", "environment", "aware", "present", "detached", "distant"],
                context_hints=["how do you feel about your surroundings", "do you feel present", "how aware are you"]
            ),
            Question(
                id=3,
                category=Category.APPEARANCE_AWARENESS,
                text="Over the past two weeks, how would you describe your awareness and response to everyday situations?",
                options={
                    "A": "Alert and responsive – Quickly noticed and responded appropriately",
                    "B": "Mildly distracted – Occasionally missed details but could still participate",
                    "C": "Often preoccupied – Frequently lost in thought, slow or inappropriate responses",
                    "D": "Unaware or withdrawn – Rarely engaged or aware of what was happening"
                },
                keywords=["aware", "alert", "responsive", "distracted", "preoccupied", "withdrawn"],
                context_hints=["how do you respond to situations", "how aware are you of what's happening"]
            ),
            # Attitude & Engagement
            Question(
                id=4,
                category=Category.ATTITUDE_ENGAGEMENT,
                text="How do you generally respond when someone asks for your opinion?",
                options={
                    "A": "I respond openly and constructively",
                    "B": "I avoid giving direct answers",
                    "C": "I question their intent before answering",
                    "D": "I refuse to answer or challenge the question"
                },
                keywords=["opinion", "respond", "answer", "question", "avoid", "challenge"],
                context_hints=["how do you give your opinion", "what do you do when asked for your thoughts"]
            ),
            Question(
                id=5,
                category=Category.ATTITUDE_ENGAGEMENT,
                text="How do you maintain eye contact in a conversation?",
                options={
                    "A": "I maintain steady and appropriate eye contact",
                    "B": "I look around frequently or avoid direct gaze",
                    "C": "I maintain eye contact but remain reserved",
                    "D": "I stare intensely or aggressively"
                },
                keywords=["eye contact", "look", "gaze", "stare", "eyes"],
                context_hints=["how do you look at people", "do you make eye contact"]
            ),
            Question(
                id=6,
                category=Category.ATTITUDE_ENGAGEMENT,
                text="How do you generally move or use gestures when interacting?",
                options={
                    "A": "I use natural gestures that match my speech",
                    "B": "I fidget or avoid noticeable movement",
                    "C": "I keep my movements restricted or deliberate",
                    "D": "I use abrupt or forceful gestures"
                },
                keywords=["gesture", "move", "fidget", "restricted", "forceful", "body language"],
                context_hints=["how do you move when talking", "what do you do with your hands"]
            ),
            # Behavior and Performance
            Question(
                id=7,
                category=Category.BEHAVIOR_PERFORMANCE,
                text="How did it feel when you spoke to people during recent conversations?",
                options={
                    "A": "Pretty normal, nothing different",
                    "B": "A bit faster than usual, but still clear",
                    "C": "Like I have to think a bit more before I speak",
                    "D": "Like words tumble out before I've fully thought them through"
                },
                keywords=["speak", "talk", "conversation", "words", "think", "clear"],
                context_hints=["how do you feel when talking", "how do you speak in conversations"]
            ),
            Question(
                id=8,
                category=Category.BEHAVIOR_PERFORMANCE,
                text="How do you usually respond to a rough day?",
                options={
                    "A": "I shake it off pretty easily and move on",
                    "B": "I get upset, but remind myself it'll pass and keep going",
                    "C": "I try! But it often feels like what I do doesn't matter",
                    "D": "I feel like it's all too much, and nothing I do will really change things"
                },
                keywords=["rough day", "upset", "shake off", "overwhelm", "cope", "handle"],
                context_hints=["how do you deal with bad days", "what do you do when things go wrong"]
            ),
            Question(
                id=9,
                category=Category.BEHAVIOR_PERFORMANCE,
                text="What usually happens when you start speaking in a meeting?",
                options={
                    "A": "I give an update with key points in order",
                    "B": "I pause to collect my thoughts, then explain things",
                    "C": "I start talking but lose track or forget important details",
                    "D": "I struggle to find the right words and jump between unrelated points"
                },
                keywords=["meeting", "speak", "explain", "thoughts", "track", "words"],
                context_hints=["how do you speak in meetings", "what happens when you present"]
            ),
            # Somatic Complaints
            Question(
                id=10,
                category=Category.SOMATIC_COMPLAINTS,
                text="How often have you felt unexplained physical pain recently?",
                options={
                    "A": "Not at all – I haven't experienced any such pain",
                    "B": "Occasionally – I've felt some discomfort, but it's rare and manageable",
                    "C": "Frequently – These symptoms happen a few times a week and are noticeable",
                    "D": "Almost daily – The physical discomfort is regular and affecting my routine"
                },
                keywords=["pain", "ache", "headache", "discomfort", "physical", "body"],
                context_hints=["do you have any pain", "how's your body feeling", "any physical discomfort"]
            ),
            Question(
                id=11,
                category=Category.SOMATIC_COMPLAINTS,
                text="Do you experience stomach issues during stress or deadlines?",
                options={
                    "A": "Rarely – My digestion stays the same regardless of stress",
                    "B": "Sometimes – I notice mild symptoms when I'm under pressure",
                    "C": "Often – My stomach tends to get upset during high-stress situations",
                    "D": "Very frequently – I almost always experience digestive issues during deadlines"
                },
                keywords=["stomach", "digestion", "stress", "deadline", "upset", "bloating"],
                context_hints=["how's your stomach", "do you get digestive issues", "how do you feel during stress"]
            ),
            Question(
                id=12,
                category=Category.SOMATIC_COMPLAINTS,
                text="How often do you feel tired or physically drained?",
                options={
                    "A": "Almost never – I usually wake up refreshed and energized",
                    "B": "Occasionally – I feel tired once in a while but bounce back quickly",
                    "C": "Often – I feel low on energy most days, even without a clear reason",
                    "D": "Almost always – I feel physically exhausted even when I've rested well"
                },
                keywords=["tired", "energy", "drained", "exhausted", "rest", "sleep"],
                context_hints=["how's your energy", "do you feel tired", "how do you feel after sleeping"]
            )
        ]
        self.current_answers = {q.id: None for q in self.questions}
    
    def get_unanswered_questions(self) -> List[Question]:
        """Return questions that haven't been answered yet."""
        return [q for q in self.questions if self.current_answers[q.id] is None]
    
    def get_category_score(self, category: Category) -> float:
        """Calculate the average score for a category (A=4, B=3, C=2, D=1)."""
        category_questions = [q for q in self.questions if q.category == category]
        if not category_questions:
            return 0.0
        
        total_score = 0
        answered_count = 0
        
        for q in category_questions:
            answer_data = self.current_answers[q.id]
            if answer_data:
                answer = answer_data['answer']
                score = ord('D') - ord(answer) + 1  # A=4, B=3, C=2, D=1
                total_score += score
                answered_count += 1
        
        return total_score / answered_count if answered_count > 0 else 0.0
    
    def get_completion_percentage(self) -> float:
        """Return the percentage of questions that have been answered."""
        answered = sum(1 for answer in self.current_answers.values() if answer is not None)
        return (answered / len(self.questions)) * 100 