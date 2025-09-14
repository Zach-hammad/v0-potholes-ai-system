from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import get_current_user
import os
import json
import openai

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Initialize OpenAI client if API key is available
openai_client = None
if os.getenv('OPENAI_API_KEY'):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    openai_client = openai

@chat_bp.route('/')
def index():
    """Chat interface"""
    user = get_current_user()
    return render_template('chat/index.html', user=user)

@chat_bp.route('/api/message', methods=['POST'])
def send_message():
    """Handle chat messages"""
    if not openai_client:
        return jsonify({
            'error': 'AI service not configured. Please contact administrator.',
            'fallback': True
        }), 503
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get chat history from session
        chat_history = session.get('chat_history', [])
        
        # Add user message to history
        chat_history.append({'role': 'user', 'content': user_message})
        
        # Prepare system prompt for POTHOLES context
        system_prompt = """You are POTHOLES AI Assistant, a helpful chatbot for a pothole detection and management system. 
        You can help users with:
        - Understanding how to report potholes
        - Explaining the pothole detection process
        - Providing information about incident status
        - General questions about road maintenance
        - Navigation help for the POTHOLES system
        
        Keep responses concise, helpful, and focused on pothole-related topics. If asked about unrelated topics, 
        politely redirect to pothole management assistance."""
        
        # Prepare messages for OpenAI
        messages = [{'role': 'system', 'content': system_prompt}]
        messages.extend(chat_history[-10:])  # Keep last 10 messages for context
        
        # Get AI response
        response = openai.ChatCompletion.create(
            model=os.getenv('AI_MODEL', 'gpt-3.5-turbo'),
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_message = response.choices[0].message.content
        
        # Add AI response to history
        chat_history.append({'role': 'assistant', 'content': ai_message})
        
        # Keep only last 20 messages in session
        session['chat_history'] = chat_history[-20:]
        
        return jsonify({
            'message': ai_message,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'AI service error: {str(e)}',
            'fallback': True
        }), 500

@chat_bp.route('/api/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    session.pop('chat_history', None)
    return jsonify({'success': True})

@chat_bp.route('/api/suggestions')
def get_suggestions():
    """Get suggested questions"""
    suggestions = [
        "How do I report a pothole?",
        "What information do I need to provide?",
        "How long does it take to fix a pothole?",
        "Can I check the status of my report?",
        "What makes a pothole high priority?",
        "How does the AI detection work?",
        "Who can I contact for urgent issues?",
        "How do I use the map feature?"
    ]
    return jsonify({'suggestions': suggestions})

def get_fallback_response(message):
    """Provide fallback responses when AI is not available"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['report', 'submit', 'new']):
        return "To report a pothole, visit our reporting page and provide the location, description, and photos if possible. Our team will review and prioritize your report."
    
    elif any(word in message_lower for word in ['status', 'check', 'update']):
        return "You can check the status of reported potholes on our map view. Each incident shows its current status and priority level."
    
    elif any(word in message_lower for word in ['priority', 'urgent', 'emergency']):
        return "Pothole priority is determined by factors like size, location, traffic volume, and safety risk. Emergency issues affecting major roads get highest priority."
    
    elif any(word in message_lower for word in ['contact', 'help', 'support']):
        return "For additional help, you can contact our support team through the contact form or reach out to your local road maintenance department."
    
    elif any(word in message_lower for word in ['ai', 'detection', 'how', 'work']):
        return "Our AI system analyzes images and sensor data to automatically detect and classify potholes, helping prioritize repairs based on severity and location."
    
    else:
        return "I'm here to help with pothole reporting and management questions. You can ask about reporting procedures, checking status, or how our system works."
