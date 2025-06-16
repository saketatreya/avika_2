# Mental Health Assessment Chatbot

A conversational chatbot that conducts a mental health assessment through natural dialogue using the Google Gemini API. The chatbot gathers information about a person's mental state by engaging in natural conversation, without explicitly asking questionnaire questions.

## Features

- Natural conversation-based assessment
- Implicit information gathering
- Empathetic and supportive dialogue
- Comprehensive mental health evaluation
- Beautiful web interface with real-time updates
- Interactive progress tracking
- Visual assessment results
- Responsive design for all devices

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

### Web Interface

1. Make sure your virtual environment is activated
2. Start the web server:
```bash
python app.py
```
3. Open your web browser and navigate to `http://localhost:5000`
4. Start chatting! The interface includes:
   - Real-time chat window
   - Progress tracking
   - Category-wise assessment
   - Visual results with radar chart
   - Detailed assessment breakdown

### Command Line Interface

Alternatively, you can use the command-line interface:
```bash
python chatbot.py
```

## Web Interface Features

- **Real-time Chat**: Smooth, animated chat interface with message history
- **Progress Tracking**: Visual progress indicator showing assessment completion
- **Category Progress**: Individual progress bars for each assessment category
- **Results Visualization**: 
  - Radar chart showing scores across categories
  - Detailed breakdown of questions and answers
  - Color-coded scoring system
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Accessibility**: High contrast, readable text, and keyboard navigation

## How It Works

The chatbot uses the Google Gemini API to:
1. Maintain natural conversation
2. Analyze responses for relevant information
3. Map responses to questionnaire options
4. Generate empathetic and supportive replies

The assessment is conducted through four main categories:
1. Appearance & Awareness
2. Attitude & Engagement
3. Behavior and Performance
4. Somatic Complaints

Each category is scored on a scale of 1-4, with detailed results provided at the end of the assessment.

## Technical Details

- **Backend**: Flask with Socket.IO for real-time communication
- **Frontend**: 
  - HTML5 with Tailwind CSS for styling
  - Socket.IO for real-time updates
  - Chart.js for data visualization
  - Responsive design with mobile-first approach
- **Real-time Features**:
  - WebSocket communication
  - Progress updates
  - Instant message delivery
  - Dynamic results display

## Privacy and Ethics

- All conversations are processed locally and not stored
- The chatbot is designed to be supportive and non-judgmental
- No personal information is collected or stored
- The assessment is not a substitute for professional medical advice

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 