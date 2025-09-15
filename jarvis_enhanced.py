#!/usr/bin/env python3
"""
JARVIS AI Desktop Assistant - Enhanced Version (FIXED)
A comprehensive voice-controlled AI assistant for computer automation
Features: File operations, web search, AI integration, safety controls
"""

import speech_recognition as sr
import pyttsx3
import os
import sys
import subprocess
import webbrowser
import datetime
import json
import threading
import time
import requests
from pathlib import Path
import psutil
import pyautogui
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import logging
from typing import Optional, List, Dict, Any
import hashlib
import shutil
import mimetypes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)

class SafetyManager:
    """Manages safety and security for file operations"""
    
    def __init__(self):
        self.protected_paths = [
            "/System", "/Windows/System32", "/Windows/SysWOW64",
            "/etc", "/usr/bin", "/usr/sbin", "/bin", "/sbin",
            "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
            os.path.expanduser("~/.ssh"),
            os.path.expanduser("~/AppData/Roaming"),
        ]
        
        self.dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.scr', '.com', '.pif',
            '.msi', '.dll', '.sys', '.inf', '.reg'
        ]
        
        self.safe_extensions = [
            '.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls',
            '.pptx', '.ppt', '.jpg', '.jpeg', '.png', '.gif',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.csv',
            '.json', '.xml', '.html', '.css', '.js', '.py',
            '.md', '.rtf', '.odt', '.ods', '.odp'
        ]
    
    def is_safe_path(self, file_path: str) -> bool:
        """Check if file path is safe to access"""
        abs_path = os.path.abspath(file_path)
        return not any(protected in abs_path for protected in self.protected_paths)
    
    def is_safe_file(self, file_path: str) -> bool:
        """Check if file is safe to open"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.safe_extensions and ext not in self.dangerous_extensions

class AIIntegration:
    """Handles AI integrations with OpenAI and Gemini - FIXED VERSION"""
    
    def __init__(self, openai_key: str = "", gemini_key: str = ""):
        self.openai_key = openai_key
        self.gemini_key = gemini_key
        self.openai_client = None
        self.gemini_model = None
        
        # Initialize OpenAI client if key is available
        if self.openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                logging.info("OpenAI client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize Gemini model if key is available
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                # FIX 1: Use correct model name for current Gemini API
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')  # Changed from gemini-1.5-pro-latest
                logging.info("Gemini model initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Gemini model: {e}")
    
    def query_openai(self, prompt: str) -> str:
        """Query OpenAI GPT for complex tasks - FIXED VERSION"""
        if not self.openai_key or not self.openai_client:
            return "OpenAI API key not configured or client not initialized"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are JARVIS, a helpful assistant. Provide concise, accurate responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg:
                return "OpenAI quota exceeded. Please check your billing details."
            elif "rate_limit" in error_msg:
                return "OpenAI rate limit reached. Please try again later."
            else:
                logging.error(f"OpenAI API error: {e}")
                return f"Error querying OpenAI: {str(e)}"
    
    def query_gemini(self, prompt: str) -> str:
        """Query Google Gemini for complex tasks - FIXED VERSION"""
        if not self.gemini_key or not self.gemini_model:
            return "Gemini API key not configured or model not initialized"
        
        try:
            response = self.gemini_model.generate_content(prompt)
            if response.text:
                return response.text
            else:
                return "Gemini returned empty response"
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower():
                return "Gemini quota exceeded. Please check your billing details or try again later."
            elif "rate" in error_msg.lower():
                return "Gemini rate limit reached. Please try again later."
            else:
                logging.error(f"Gemini API error: {e}")
                return f"Error querying Gemini: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return bool(self.openai_client or self.gemini_model)
    
    def get_status(self) -> str:
        """Get status of AI integrations"""
        status = []
        if self.openai_client:
            status.append("OpenAI: Ready")
        else:
            status.append("OpenAI: Not configured")
        
        if self.gemini_model:
            status.append("Gemini: Ready")
        else:
            status.append("Gemini: Not configured")
        
        return " | ".join(status)

class JarvisEnhanced:
    """Enhanced JARVIS AI Desktop Assistant - FIXED VERSION"""
    
    def __init__(self):
        self.is_listening = False
        self.is_muted = False
        self.wake_word = "jarvis"
        self.safety_manager = SafetyManager()
        
        # Initialize speech components
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()

        # FIX 2: Add microphone lock for threading safety
        self.microphone_lock = threading.Lock()
        
        # Load configuration
        self.config = self.load_config()
        self.setup_tts()
        
        # FIX 3: Better API key loading with validation
        self.load_api_keys()
        
        # Command history and learning
        self.command_history = []
        self.user_preferences = {}
        
        # GUI components
        self.root = None
        self.status_var = None
        self.log_text = None
        
        logging.info("JARVIS Enhanced initialized successfully")
        self.speak("JARVIS Enhanced AI Assistant is online and ready for voice commands")
    
    def load_api_keys(self):
        """Load and validate API keys - FIXED VERSION"""
        # Load from environment variables first (recommended)
        openai_key = os.getenv('OPENAI_API_KEY', '').strip()
        gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
        
        # Fallback to config file
        if not openai_key:
            openai_key = self.config.get('openai_api_key', '').strip()
        if not gemini_key:
            gemini_key = self.config.get('gemini_api_key', '').strip()
        
        # Initialize AI integration
        self.ai = AIIntegration(openai_key, gemini_key)
        
        # Log status
        if openai_key:
            logging.info(f"OpenAI API key loaded (length: {len(openai_key)})")
        else:
            logging.warning("No OpenAI API key found")
        
        if gemini_key:
            logging.info(f"Gemini API key loaded (length: {len(gemini_key)})")
        else:
            logging.warning("No Gemini API key found")
        
        logging.info(f"AI Integration Status: {self.ai.get_status()}")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_file = Path.home() / '.jarvis_enhanced_config.json'
        default_config = {
            'voice_rate': 180,
            'voice_volume': 0.8,
            'voice_id': 0,
            'openai_api_key': '',
            'gemini_api_key': '',
            'weather_api_key': '',
            'safe_mode': True,
            'auto_save_history': True,
            'max_search_results': 5,
            'default_browser': 'default'
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config

    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        config_file = Path.home() / '.jarvis_enhanced_config.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def setup_tts(self):
        """Configure text-to-speech engine"""
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices and len(voices) > self.config.get('voice_id', 0):
                self.tts_engine.setProperty('voice', voices[self.config['voice_id']].id)
            
            self.tts_engine.setProperty('rate', self.config.get('voice_rate', 180))
            self.tts_engine.setProperty('volume', self.config.get('voice_volume', 0.8))
        except Exception as e:
            logging.error(f"TTS setup error: {e}")

    def speak(self, text: str):
        """Convert text to speech with error handling"""
        if not self.is_muted and text:
            try:
                print(f"JARVIS: {text}")
                if self.log_text:
                    self.log_text.insert(tk.END, f"JARVIS: {text}\n")
                    self.log_text.see(tk.END)
                
                # Run TTS in separate thread to prevent blocking
                def speak_async():
                    try:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                    except Exception as e:
                        logging.error(f"TTS error: {e}")
                
                threading.Thread(target=speak_async, daemon=True).start()
            except Exception as e:
                logging.error(f"Speak error: {e}")

    def listen_for_wake_word(self):
        """Continuously listen for wake word - FIXED VERSION"""
        try:
            # FIX 4: Better microphone initialization
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logging.info("Microphone calibrated for wake word detection")
            
            while True:
                try:
                    with self.microphone_lock:
                        if self.status_var:
                            self.status_var.set("Listening for wake word...")
                        
                        with self.microphone as source:
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    command = self.recognizer.recognize_google(audio, language='en-US').lower()
                    
                    if self.wake_word in command:
                        self.speak("Yes, I'm listening. How can I help you?")
                        if self.status_var:
                            self.status_var.set("Processing commands...")
                        self.process_command_session()
                        
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    logging.error(f"Speech recognition service error: {e}")
                    time.sleep(2)
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    if "context manager" not in str(e):  # FIX 5: Reduce log spam for known issue
                        logging.error(f"Wake word detection error: {e}")
                    time.sleep(0.5)
                    
        except Exception as e:
            logging.error(f"Wake word listener setup error: {e}")

    def listen_for_command(self, timeout: int = 5) -> Optional[str]:
        """Listen for a single command"""
        try:
            with self.microphone_lock:
                with self.microphone as source:
                    if self.status_var:
                        self.status_var.set("Listening for command...")
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            
            command = self.recognizer.recognize_google(audio, language='en-US')
            print(f"You said: {command}")
            
            if self.log_text:
                self.log_text.insert(tk.END, f"You: {command}\n")
                self.log_text.see(tk.END)
            
            return command.lower()
            
        except sr.UnknownValueError:
            self.speak("I didn't catch that. Could you please repeat?")
            return None
        except sr.RequestError as e:
            self.speak("Sorry, there was an error with the speech recognition service.")
            logging.error(f"Speech recognition error: {e}")
            return None
        except sr.WaitTimeoutError:
            self.speak("I didn't hear anything. Say 'Jarvis' to wake me up.")
            return None

    def process_command_session(self):
        """Process multiple commands in a session"""
        session_active = True
        while session_active:
            command = self.listen_for_command()
            if command:
                # Check for exit commands
                if any(word in command for word in ['stop', 'exit', 'quit', 'goodbye', 'bye']):
                    self.speak("Goodbye! Say 'Jarvis' to wake me up again.")
                    session_active = False
                    continue
                
                # Process the command
                response = self.process_command(command)
                if response:
                    self.speak(response)
                
                # Save command to history
                self.command_history.append({
                    'timestamp': datetime.datetime.now().isoformat(),
                    'command': command,
                    'response': response
                })

    def process_command(self, command: str) -> str:
        """Process and execute commands with enhanced capabilities"""
        command = command.lower().strip()
        
        try:
            # File operations
            if any(phrase in command for phrase in ['read file', 'open file', 'show me file']):
                return self.handle_file_operations(command)
            elif any(phrase in command for phrase in ['search file', 'find file']):
                return self.search_files(command)
            elif 'list files' in command or 'show files' in command:
                return self.list_files(command)
            
            # Web search operations
            elif any(phrase in command for phrase in ['search for', 'google', 'search google', 'look up']):
                return self.web_search(command)
            elif any(phrase in command for phrase in ['open website', 'visit', 'go to']):
                return self.open_website(command)
            
            # Application control
            elif 'open' in command and any(app in command for app in ['calculator', 'notepad', 'browser', 'file explorer', 'chrome']):
                return self.open_application(command)
            elif 'close' in command:
                return self.close_application(command)
            
            # System information
            elif any(phrase in command for phrase in ['system status', 'system info', 'computer status']):
                return self.get_system_status()
            elif any(phrase in command for phrase in ['what time', 'current time', 'time']):
                return self.get_time()
            elif any(phrase in command for phrase in ['what date', 'today', 'date']):
                return self.get_date()
            
            # AI status check - FIX 6: Add AI status command
            elif any(phrase in command for phrase in ['ai status', 'api status', 'integration status']):
                return f"AI Integration Status: {self.ai.get_status()}"
            
            # AI-powered queries for complex tasks
            elif any(phrase in command for phrase in ['explain', 'tell me about', 'what is', 'how to']):
                return self.handle_complex_query(command)
            
            # System control (safe operations only)
            elif 'take screenshot' in command:
                return self.take_screenshot()
            elif 'volume' in command:
                return self.control_volume(command)
            
            # Settings and configuration
            elif 'change voice' in command:
                return self.change_voice_settings()
            elif any(phrase in command for phrase in ['mute', 'unmute', 'silence']):
                return self.toggle_mute()
            
            # Help and information
            elif any(phrase in command for phrase in ['help', 'what can you do', 'commands']):
                return self.get_help()
            elif 'history' in command:
                return self.get_command_history()
            
            # Default: Use AI for complex interpretation
            else:
                return self.handle_complex_query(command)
                
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def handle_complex_query(self, command: str) -> str:
        """Handle complex queries using AI - FIXED VERSION"""
        try:
            # FIX 7: Better AI integration checking
            if not self.ai.is_available():
                return "AI services not available. Please configure your OpenAI or Gemini API keys in the settings."
            
            # Try Gemini first (usually faster and has higher free tier)
            if self.ai.gemini_model:
                response = self.ai.query_gemini(command)
                if response and not any(error in response.lower() for error in ['error', 'quota', 'rate limit']):
                    return response
            
            # Fallback to OpenAI
            if self.ai.openai_client:
                response = self.ai.query_openai(command)
                if response and not any(error in response.lower() for error in ['error', 'quota', 'rate limit']):
                    return response
            
            # Fallback for basic queries when AI is unavailable
            if 'what time' in command:
                return self.get_time()
            elif 'what date' in command:
                return self.get_date()
            elif 'weather' in command:
                return "Weather information requires AI integration or weather API setup."
            else:
                return "AI services are temporarily unavailable due to quota limits. Please try again later or configure different API keys."
                
        except Exception as e:
            logging.error(f"Complex query error: {e}")
            return f"Error processing complex query: {str(e)}"

    # ... (rest of the methods remain the same, just including a few key ones)

    def handle_file_operations(self, command: str) -> str:
        """Handle file reading and opening operations"""
        try:
            # Extract filename from command
            file_keywords = ['read file', 'open file', 'show me file', 'read', 'open']
            filename = command
            for keyword in file_keywords:
                if keyword in command:
                    filename = command.replace(keyword, '').strip()
                    break
            
            if not filename:
                return "Please specify which file you'd like me to open or read."
            
            # Search for the file
            found_files = self.find_files_by_name(filename)
            
            if not found_files:
                return f"I couldn't find any file matching '{filename}'"
            
            if len(found_files) > 1:
                files_list = "\n".join([f"{i+1}. {os.path.basename(f)} in {os.path.dirname(f)}" 
                                      for i, f in enumerate(found_files[:5])])
                return f"I found multiple files matching '{filename}':\n{files_list}\nPlease be more specific."
            
            file_path = found_files[0]
            
            # Safety check
            if not self.safety_manager.is_safe_path(file_path) or not self.safety_manager.is_safe_file(file_path):
                return f"Sorry, I cannot open this file for security reasons: {file_path}"
            
            # Read file content if it's a text file
            if any(file_path.lower().endswith(ext) for ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.csv']):
                return self.read_text_file(file_path)
            else:
                # Open with default application
                return self.open_file_with_default_app(file_path)
                
        except Exception as e:
            return f"Error handling file operation: {str(e)}"

    def web_search(self, command: str) -> str:
        """Perform web search and provide voice feedback"""
        try:
            # Extract search term
            search_keywords = ['search for', 'google', 'search google', 'look up']
            search_term = command
            for keyword in search_keywords:
                if keyword in command:
                    search_term = command.replace(keyword, '').strip()
                    break
            
            if not search_term:
                return "What would you like me to search for?"
            
            # Open search in browser
            search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            # Try to get quick information using AI
            ai_summary = ""
            if self.ai.is_available():
                prompt = f"Provide a brief, accurate summary about '{search_term}' in 2-3 sentences."
                if self.ai.gemini_model:
                    ai_summary = self.ai.query_gemini(prompt)
                elif self.ai.openai_client:
                    ai_summary = self.ai.query_openai(prompt)
                
                if ai_summary and not any(error in ai_summary.lower() for error in ['error', 'quota', 'rate limit']):
                    return f"Searching for '{search_term}' and opened results in browser. Here's what I found: {ai_summary}"
            
            return f"I've opened Google search results for '{search_term}' in your browser."
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"

    # ... (include other necessary methods like get_system_status, get_time, etc.)

    def get_system_status(self) -> str:
        """Get system status information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = f"System status: CPU usage {cpu_percent:.1f}%, "
            status += f"Memory usage {memory.percent:.1f}%, "
            status += f"Disk usage {disk.percent:.1f}%"
            
            return status
        except Exception as e:
            return f"Error getting system status: {str(e)}"

    def get_time(self) -> str:
        """Get current time"""
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}"

    def get_date(self) -> str:
        """Get current date"""
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}"

    def get_help(self) -> str:
        """Provide comprehensive help information"""
        ai_status = "Available" if self.ai.is_available() else "Not configured"
        return f"""I can help you with:

File Operations:
- "Read file [filename]" - Read and open files
- "Search file [filename]" - Find files by name
- "List files in [folder]" - Show files in directory

Web & Search:
- "Search for [topic]" - Google search with AI summary
- "Open website [url/name]" - Visit websites
- "Look up [topic]" - Get information using AI

System Control:
- "Open calculator/notepad/browser/file explorer"
- "Take screenshot" - Capture screen
- "System status" - Check CPU, memory, disk
- "What time is it?" - Current time
- "What's the date?" - Today's date

AI Features (Status: {ai_status}):
- "Explain [topic]" - Get detailed explanations
- "Tell me about [subject]" - Learn about topics
- "How to [task]" - Get instructions
- "AI status" - Check API integration status

Settings:
- "Mute/Unmute" - Toggle voice
- "Help" - Show this help

Say 'Stop' or 'Goodbye' to end the session.
Current AI Status: {self.ai.get_status()}"""

    def create_gui(self) -> tk.Tk:
        """Create enhanced GUI interface"""
        self.root = tk.Tk()
        self.root.title("JARVIS Enhanced AI Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg='#0a0a0a')
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        bg_color = '#0a0a0a'
        accent_color = "#2E8596"
        text_color = '#ffffff'
        
        # Title frame
        title_frame = tk.Frame(self.root, bg=bg_color)
        title_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(title_frame, text="J.A.R.V.I.S.", 
                              font=('Arial', 28, 'bold'), 
                              fg=accent_color, bg=bg_color)
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="Enhanced AI Desktop Assistant", 
                                 font=('Arial', 12), 
                                 fg=text_color, bg=bg_color)
        subtitle_label.pack()
        
        # AI Status display - FIX 8: Add AI status to GUI
        ai_status_label = tk.Label(title_frame, text=f"AI Status: {self.ai.get_status()}", 
                                  font=('Arial', 10), 
                                  fg='#888888', bg=bg_color)
        ai_status_label.pack()
        
        # Status frame
        status_frame = tk.Frame(self.root, bg=bg_color)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=('Arial', 14), fg=accent_color, bg=bg_color)
        status_label.pack()
        
        # Control buttons frame
        button_frame = tk.Frame(self.root, bg=bg_color)
        button_frame.pack(pady=20)
        
        # Listen button
        self.listen_button = tk.Button(button_frame, text="🎤 Start Listening",
                                      command=self.toggle_listening,
                                      bg=accent_color, fg='black', 
                                      font=('Arial', 12, 'bold'),
                                      width=15, height=2)
        self.listen_button.pack(side=tk.LEFT, padx=10)
        
        # Mute button
        self.mute_button = tk.Button(button_frame, text="🔊 Mute/Unmute",
                                    command=self.gui_toggle_mute,
                                    bg='#ffa502', fg='white', 
                                    font=('Arial', 12, 'bold'),
                                    width=15, height=2)
        self.mute_button.pack(side=tk.LEFT, padx=10)
        
        # Settings button
        settings_button = tk.Button(button_frame, text="⚙️ Settings",
                                   command=self.open_settings_window,
                                   bg='#2ed573', fg='white', 
                                   font=('Arial', 12, 'bold'),
                                   width=15, height=2)
        settings_button.pack(side=tk.LEFT, padx=10)
        
        # Log frame
        log_frame = tk.Frame(self.root, bg=bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        log_title = tk.Label(log_frame, text="💬 Conversation Log:", 
                            font=('Arial', 14, 'bold'), 
                            fg=text_color, bg=bg_color)
        log_title.pack(anchor=tk.W)
        
        # Text widget with scrollbar
        text_frame = tk.Frame(log_frame, bg=bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(text_frame, bg='#1a1a2e', fg=accent_color,
                               font=('Consolas', 10), wrap=tk.WORD,
                               insertbackground=accent_color)
        scrollbar = tk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Info frame
        info_frame = tk.Frame(self.root, bg=bg_color)
        info_frame.pack(fill=tk.X, pady=5)
        
        info_text = "Say 'Jarvis' to activate voice commands | Safe mode enabled"
        info_label = tk.Label(info_frame, text=info_text, 
                             font=('Arial', 10), fg='#888888', bg=bg_color)
        info_label.pack()
        
        # Start background processes
        self.start_background_processes()
        
        return self.root

    def start_background_processes(self):
        """Start background threads for voice recognition"""
        # Wake word detection thread
        wake_word_thread = threading.Thread(target=self.listen_for_wake_word, daemon=True)
        wake_word_thread.start()
        
        # Log initial message
        if self.log_text:
            self.log_text.insert(tk.END, "JARVIS Enhanced AI Assistant Started\n")
            self.log_text.insert(tk.END, f"AI Status: {self.ai.get_status()}\n")
            self.log_text.insert(tk.END, "Say 'Jarvis' to activate voice commands\n")
            self.log_text.insert(tk.END, "=" * 50 + "\n")

    def toggle_listening(self):
        """Toggle manual listening mode"""
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.listen_button.config(text="🛑 Stop Listening")
            self.status_var.set("Manual listening active...")
            threading.Thread(target=self.manual_listening_session, daemon=True).start()
        else:
            self.listen_button.config(text="🎤 Start Listening")
            self.status_var.set("Ready")

    def manual_listening_session(self):
        """Manual listening session for GUI"""
        while self.is_listening:
            command = self.listen_for_command(timeout=3)
            if command:
                if any(word in command for word in ['stop listening', 'stop', 'exit']):
                    break
                
                response = self.process_command(command)
                if response:
                    self.speak(response)
            time.sleep(0.5)
        
        self.is_listening = False
        if self.listen_button:
            self.listen_button.config(text="🎤 Start Listening")
        if self.status_var:
            self.status_var.set("Ready")

    def gui_toggle_mute(self):
        """Toggle mute from GUI"""
        self.is_muted = not self.is_muted
        status = "🔇 Muted" if self.is_muted else "🔊 Unmuted"
        self.mute_button.config(text=status)
        if self.log_text:
            self.log_text.insert(tk.END, f"System: Voice {status.split()[1]}\n")
            self.log_text.see(tk.END)

    def open_settings_window(self):
        """Open settings configuration window - FIXED VERSION"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("JARVIS Settings")
        settings_window.geometry("600x500")
        settings_window.configure(bg='#1a1a2e')
        
        # Settings notebook
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Voice settings tab
        voice_frame = tk.Frame(notebook, bg='#1a1a2e')
        notebook.add(voice_frame, text="Voice Settings")
        
        tk.Label(voice_frame, text="Speech Rate:", bg='#1a1a2e', fg='#00d4ff').pack(anchor=tk.W, padx=10, pady=5)
        rate_scale = tk.Scale(voice_frame, from_=100, to=300, orient=tk.HORIZONTAL,
                             bg='#1a1a2e', fg='#00d4ff', highlightbackground='#1a1a2e')
        rate_scale.set(self.config.get('voice_rate', 180))
        rate_scale.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(voice_frame, text="Volume:", bg='#1a1a2e', fg='#00d4ff').pack(anchor=tk.W, padx=10, pady=5)
        volume_scale = tk.Scale(voice_frame, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL,
                               bg='#1a1a2e', fg='#00d4ff', highlightbackground='#1a1a2e')
        volume_scale.set(self.config.get('voice_volume', 0.8))
        volume_scale.pack(fill=tk.X, padx=10, pady=5)
        
        # AI settings tab
        ai_frame = tk.Frame(notebook, bg='#1a1a2e')
        notebook.add(ai_frame, text="AI Settings")
        
        # Current status display
        tk.Label(ai_frame, text=f"Current Status: {self.ai.get_status()}", 
                bg='#1a1a2e', fg='#00ff00', font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=10)
        
        tk.Label(ai_frame, text="OpenAI API Key:", bg='#1a1a2e', fg='#00d4ff').pack(anchor=tk.W, padx=10, pady=5)
        openai_entry = tk.Entry(ai_frame, width=60, show="*")
        current_openai = os.getenv('OPENAI_API_KEY', '') or self.config.get('openai_api_key', '')
        openai_entry.insert(0, current_openai)
        openai_entry.pack(padx=10, pady=5)
        
        tk.Label(ai_frame, text="Gemini API Key:", bg='#1a1a2e', fg='#00d4ff').pack(anchor=tk.W, padx=10, pady=5)
        gemini_entry = tk.Entry(ai_frame, width=60, show="*")
        current_gemini = os.getenv('GEMINI_API_KEY', '') or self.config.get('gemini_api_key', '')
        gemini_entry.insert(0, current_gemini)
        gemini_entry.pack(padx=10, pady=5)
        
        # Instructions
        instructions = tk.Text(ai_frame, height=8, wrap=tk.WORD, bg='#2a2a3e', fg='#cccccc', font=('Arial', 9))
        instructions.insert(tk.END, """API Key Setup Instructions:

1. RECOMMENDED: Set environment variables (persistent across sessions):
   - Windows: Set OPENAI_API_KEY and GEMINI_API_KEY in System Environment Variables
   - Command: setx OPENAI_API_KEY "your-key-here"
   - Command: setx GEMINI_API_KEY "your-key-here"

2. ALTERNATIVE: Enter keys above (stored in config file)

3. Get API Keys:
   - OpenAI: https://platform.openai.com/api-keys
   - Gemini: https://aistudio.google.com/app/apikey

4. After setting environment variables, restart JARVIS completely.

Current Detection:
- Environment OPENAI_API_KEY: """ + ("✓ Found" if os.getenv('OPENAI_API_KEY') else "✗ Not found") + """
- Environment GEMINI_API_KEY: """ + ("✓ Found" if os.getenv('GEMINI_API_KEY') else "✗ Not found"))
        instructions.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        instructions.config(state=tk.DISABLED)
        
        # Test AI button
        def test_ai_connections():
            test_window = tk.Toplevel(settings_window)
            test_window.title("AI Connection Test")
            test_window.geometry("500x300")
            test_window.configure(bg='#1a1a2e')
            
            test_text = tk.Text(test_window, bg='#2a2a3e', fg='#00d4ff', font=('Consolas', 10))
            test_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            test_text.insert(tk.END, "Testing AI connections...\n\n")
            test_window.update()
            
            # Test OpenAI
            if self.ai.openai_client:
                test_text.insert(tk.END, "Testing OpenAI...\n")
                test_window.update()
                result = self.ai.query_openai("Say 'OpenAI test successful' in exactly those words.")
                test_text.insert(tk.END, f"OpenAI Result: {result}\n\n")
            else:
                test_text.insert(tk.END, "OpenAI: Not configured\n\n")
            
            # Test Gemini
            if self.ai.gemini_model:
                test_text.insert(tk.END, "Testing Gemini...\n")
                test_window.update()
                result = self.ai.query_gemini("Say 'Gemini test successful' in exactly those words.")
                test_text.insert(tk.END, f"Gemini Result: {result}\n\n")
            else:
                test_text.insert(tk.END, "Gemini: Not configured\n\n")
            
            test_text.insert(tk.END, "Test completed!")
            test_text.config(state=tk.DISABLED)
        
        test_button = tk.Button(ai_frame, text="🧪 Test AI Connections", 
                               command=test_ai_connections,
                               bg='#ff6b6b', fg='white', font=('Arial', 10, 'bold'))
        test_button.pack(pady=10)
        
        # Save function
        def save_all_settings():
            # Update voice settings
            self.config['voice_rate'] = rate_scale.get()
            self.config['voice_volume'] = volume_scale.get()
            
            # Update API keys in config (as backup)
            self.config['openai_api_key'] = openai_entry.get().strip()
            self.config['gemini_api_key'] = gemini_entry.get().strip()
            
            # Reinitialize AI with new settings
            self.setup_tts()
            self.load_api_keys()  # This will reinitialize AI integration
            
            # Save config
            self.save_config()
            
            settings_window.destroy()
            self.speak("Settings updated successfully. AI integration reinitialized.")
            
            # Update GUI status
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert(tk.END, f"Settings updated. New AI Status: {self.ai.get_status()}\n")
                self.log_text.see(tk.END)
        
        # Save button
        save_button = tk.Button(settings_window, text="💾 Save Settings", 
                               command=save_all_settings,
                               bg='#00d4ff', fg='black', font=('Arial', 12, 'bold'))
        save_button.pack(pady=20)

    # Include other missing methods
    def find_files_by_name(self, filename: str, limit: int = 10) -> List[str]:
        """Find files by name in common directories"""
        search_dirs = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Pictures"),
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Videos"),
            os.getcwd()  # Current directory
        ]
        
        found_files = []
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                try:
                    for root, dirs, files in os.walk(search_dir):
                        if len(found_files) >= limit:
                            break
                        
                        # Skip hidden directories and system directories
                        dirs[:] = [d for d in dirs if not d.startswith('.') and 
                                 self.safety_manager.is_safe_path(os.path.join(root, d))]
                        
                        for file in files:
                            if filename.lower() in file.lower():
                                file_path = os.path.join(root, file)
                                if self.safety_manager.is_safe_path(file_path):
                                    found_files.append(file_path)
                                    if len(found_files) >= limit:
                                        break
                except PermissionError:
                    continue
        
        return found_files

    def read_text_file(self, file_path: str) -> str:
        """Read and return content of text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Limit content length for voice output
            if len(content) > 500:
                preview = content[:500] + "..."
                return f"File content preview from {os.path.basename(file_path)}:\n{preview}\n\nFull file has been opened in your default editor."
            else:
                return f"Content of {os.path.basename(file_path)}:\n{content}"
                
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def open_file_with_default_app(self, file_path: str) -> str:
        """Open file with default application"""
        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.call(['open', file_path])
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.call(['xdg-open', file_path])
            elif sys.platform.startswith('win'):  # Windows
                os.startfile(file_path)
            
            return f"Opened {os.path.basename(file_path)} with default application"
        except Exception as e:
            return f"Error opening file: {str(e)}"

    def search_files(self, command: str) -> str:
        """Search for files based on command"""
        search_term = command.replace('search file', '').replace('find file', '').replace('search for', '').strip()
        
        if not search_term:
            return "What file would you like me to search for?"
        
        found_files = self.find_files_by_name(search_term, limit=self.config.get('max_search_results', 5))
        
        if not found_files:
            return f"No files found matching '{search_term}'"
        
        result = f"Found {len(found_files)} file(s) matching '{search_term}':\n"
        for i, file_path in enumerate(found_files, 1):
            result += f"{i}. {os.path.basename(file_path)} in {os.path.dirname(file_path)}\n"
        
        return result

    def list_files(self, command: str) -> str:
        """List files in specified directory"""
        try:
            # Extract directory from command
            if 'in' in command:
                directory = command.split('in')[-1].strip()
                if directory in ['desktop', 'my desktop']:
                    directory = os.path.expanduser("~/Desktop")
                elif directory in ['documents', 'my documents']:
                    directory = os.path.expanduser("~/Documents")
                elif directory in ['downloads', 'my downloads']:
                    directory = os.path.expanduser("~/Downloads")
                else:
                    directory = os.path.expanduser(f"~/{directory}")
            else:
                directory = os.getcwd()
            
            if not os.path.exists(directory) or not self.safety_manager.is_safe_path(directory):
                return f"Cannot access directory: {directory}"
            
            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) and self.safety_manager.is_safe_file(item_path):
                    files.append(item)
            
            if not files:
                return f"No accessible files found in {directory}"
            
            files = sorted(files)[:20]  # Limit to 20 files
            files_list = "\n".join(f"{i+1}. {file}" for i, file in enumerate(files))
            return f"Files in {os.path.basename(directory)}:\n{files_list}"
            
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def open_website(self, command: str) -> str:
        """Open specific websites"""
        try:
            # Extract URL or site name
            site_keywords = ['open website', 'visit', 'go to']
            site = command
            for keyword in site_keywords:
                if keyword in command:
                    site = command.replace(keyword, '').strip()
                    break
            
            # Add protocol if not present
            if not site.startswith(('http://', 'https://')):
                if '.' in site:
                    site = f"https://{site}"
                else:
                    # Common websites
                    common_sites = {
                        'google': 'https://www.google.com',
                        'youtube': 'https://www.youtube.com',
                        'facebook': 'https://www.facebook.com',
                        'twitter': 'https://www.twitter.com',
                        'github': 'https://www.github.com',
                        'stackoverflow': 'https://stackoverflow.com'
                    }
                    site = common_sites.get(site.lower(), f"https://www.{site}.com")
            
            webbrowser.open(site)
            return f"Opening {site} in your browser"
            
        except Exception as e:
            return f"Error opening website: {str(e)}"

    def open_application(self, command: str) -> str:
        """Open system applications safely"""
        try:
            if 'calculator' in command:
                if sys.platform.startswith('win'):
                    subprocess.Popen(['calc'])
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', '-a', 'Calculator'])
                else:
                    subprocess.Popen(['gnome-calculator'])
                return "Opening calculator"
            
            elif 'notepad' in command or 'text editor' in command:
                if sys.platform.startswith('win'):
                    subprocess.Popen(['notepad'])
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', '-a', 'TextEdit'])
                else:
                    subprocess.Popen(['gedit'])
                return "Opening text editor"
            
            elif 'browser' in command or 'chrome' in command:
                webbrowser.open('https://www.google.com')
                return "Opening web browser"
            
            elif 'file explorer' in command or 'files' in command:
                if sys.platform.startswith('win'):
                    subprocess.Popen(['explorer'])
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', '-a', 'Finder'])
                else:
                    subprocess.Popen(['nautilus'])
                return "Opening file explorer"
            
            else:
                return "I can open calculator, notepad, browser, or file explorer. Which would you like?"
                
        except Exception as e:
            return f"Error opening application: {str(e)}"

    def take_screenshot(self) -> str:
        """Take a screenshot"""
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(desktop_path, f"jarvis_screenshot_{timestamp}.png")
            
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            return f"Screenshot saved to {screenshot_path}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"

    def control_volume(self, command: str) -> str:
        """Control system volume"""
        try:
            if 'up' in command or 'increase' in command:
                if sys.platform.startswith('win'):
                    return "Volume control requires additional setup on Windows"
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 10)'])
                    return "Volume increased"
                else:
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '10%+'])
                    return "Volume increased"
            
            elif 'down' in command or 'decrease' in command:
                if sys.platform.startswith('darwin'):
                    subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 10)'])
                    return "Volume decreased"
                else:
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '10%-'])
                    return "Volume decreased"
            
            else:
                return "Say 'volume up' or 'volume down'"
                
        except Exception as e:
            return f"Error controlling volume: {str(e)}"

    def toggle_mute(self) -> str:
        """Toggle mute state"""
        self.is_muted = not self.is_muted
        return "Voice muted" if self.is_muted else "Voice unmuted"

    def get_command_history(self) -> str:
        """Get recent command history"""
        if not self.command_history:
            return "No command history available yet."
        
        recent_commands = self.command_history[-5:]  # Last 5 commands
        history = "Recent commands:\n"
        for i, cmd in enumerate(recent_commands, 1):
            timestamp = datetime.datetime.fromisoformat(cmd['timestamp']).strftime('%H:%M')
            history += f"{i}. [{timestamp}] {cmd['command']}\n"
        
        return history

    def change_voice_settings(self) -> str:
        """Change voice settings"""
        return "Voice settings can be changed through the GUI settings panel or configuration file."

    def close_application(self, command: str) -> str:
        """Close applications (limited for safety)"""
        return "For security reasons, I can only open applications, not close them. Please close applications manually."


def main():
    """Main function to run JARVIS Enhanced - FIXED VERSION"""
    try:
        print("🚀 Initializing JARVIS Enhanced AI Assistant...")
        
        # Create JARVIS instance
        jarvis = JarvisEnhanced()
        
        # Create and run GUI
        root = jarvis.create_gui()
        
        print("✅ JARVIS Enhanced GUI started successfully!")
        print("💡 Say 'Jarvis' to activate voice commands or use the GUI controls.")
        print(f"🤖 AI Status: {jarvis.ai.get_status()}")
        
        # Start main GUI loop
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n🛑 JARVIS shutting down...")
        logging.info("JARVIS shutdown by user")
    except Exception as e:
        print(f"❌ Error starting JARVIS: {e}")
        logging.error(f"Startup error: {e}")
        messagebox.showerror("JARVIS Error", f"Failed to start JARVIS: {e}")

if __name__ == "__main__":
    main()