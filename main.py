import ollama
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import pygame
import requests
import json
import psutil
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # For volume control
import keyboard  # For media controls
import spotify_local  # For Spotify integration
import wikipedia  # For quick research
import numpy as np  # For workshop calculations
import cv2  # For workshop camera feed
import pynput
import random
import threading
import difflib
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
import shutil
from bs4 import BeautifulSoup
import yaml

class JarvisLogger:
    """Advanced logging system for JARVIS"""
    def __init__(self):
        self.logger = logging.getLogger('JARVIS')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for detailed logs
        fh = logging.FileHandler('jarvis_debug.log')
        fh.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatting
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)

class JarvisAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.speaker = pyttsx3.init()
        self.speaker.setProperty('rate', 180)  # Faster speech rate because I'm always in a hurry
        self.speaker.setProperty('voice', 'english+m3')
        pygame.mixer.init()
        
        # Initialize memory system
        self.memory = self.initialize_memory()
        
        # Initialize volume control
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Track previous volume for mute/unmute functionality
        self.previous_volume = self.volume.GetMasterVolumeLevelScalar() * 100
        self.is_muted = False
        
        # Workshop mode settings
        self.workshop_mode = False
        self.music_playlist = {
            "workshop": ["AC/DC - Back In Black", "Black Sabbath - Iron Man", "Led Zeppelin - Immigrant Song"],
            "study": ["Hans Zimmer - Time", "Mozart - Symphony No. 40", "Bach - Air on G String"]
        }
        
        # Initialize workshop camera
        self.camera = None
        
        # Quick access commands
        self.shortcuts = {
            "specs": self.show_armor_specs,
            "calculations": self.run_calculations,
            "music": self.toggle_workshop_music,
            "lights": self.toggle_workshop_lights
        }
        
        # Initialize Ollama
        try:
            self.ollama = ollama.Client()
            self.speak("Ollama AI backup systems initialized")
        except Exception as e:
            self.speak("Warning: Ollama backup systems offline")
            self.ollama = None

        self.logger = JarvisLogger()

        # Initialize function registry
        self.function_registry = {}
        # Enable self-improvement mode
        self.self_improvement_enabled = True
        
        # Initialize additional modules
        self.social_media = None  # Will be initialized on first use

    def initialize_memory(self):
        """Initialize the memory system for JARVIS"""
        try:
            with open('jarvis_memory.json', 'r') as f:
                memory = json.load(f)
            return memory
        except (FileNotFoundError, json.JSONDecodeError):
            # Create a new memory structure if file doesn't exist or is corrupted
            memory = {
                "conversations": [],
                "user_preferences": {},
                "tasks": [],
                "reminders": [],
                "last_active": str(datetime.datetime.now())
            }
            self.save_memory(memory)
            return memory
            
    def save_memory(self, memory=None):
        """Save the current memory state to file"""
        if memory is None:
            memory = self.memory
        try:
            with open('jarvis_memory.json', 'w') as f:
                json.dump(memory, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save memory: {e}")
            return False

    def speak(self, text):
        print(f"JARVIS: {text}")
        # Store conversation in memory
        try:
            self.memory.setdefault("conversations", []).append({
                "speaker": "jarvis",
                "text": text,
                "timestamp": str(datetime.datetime.now())
            })
            self.save_memory()
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
        self.speaker.say(text)
        self.speaker.runAndWait()

    def listen(self):
        """Enhanced listening with extended timeout and dynamic noise adjustment"""
        try:
            with sr.Microphone() as source:
                print("Listening...")
                # Dynamically adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                try:
                    # Extended timeout and phrase time limit
                    audio = self.recognizer.listen(source, timeout=30, phrase_time_limit=60)
                    text = self.recognizer.recognize_google(audio)
                    print(f"Boss said: {text}")
                    
                    # Store user conversation in memory
                    try:
                        self.memory.setdefault("conversations", []).append({
                            "speaker": "user",
                            "text": text,
                            "timestamp": str(datetime.datetime.now())
                        })
                        self.save_memory()
                    except Exception as e:
                        self.logger.error(f"Failed to store user input in memory: {e}")
                    
                    return text.lower()
                except sr.WaitTimeoutError:
                    self.speak("Still listening, boss. Take your time.")
                    return self.listen()  # Recursively continue listening
                except sr.UnknownValueError:
                    self.speak("Could you repeat that? My audio processing isn't as good as it will be in Mark 2.")
                    return ""
                except sr.RequestError as e:
                    self.speak(f"Network issues. Error: {e}")
                    return ""
        except Exception as e:
            self.speak(f"Sorry boss, having some technical difficulties: {e}")
            return ""

    def add_function(self, function_name, code_string):
        """Dynamically add new functions to JARVIS"""
        try:
            # Validate and clean the code
            if 'import' in code_string.lower():
                self.speak("Sorry boss, can't import modules dynamically for security reasons.")
                return False
            
            # Add the function to the class
            exec(code_string)
            function_object = locals()[function_name]
            setattr(JarvisAssistant, function_name, function_object)
            
            self.speak(f"Successfully added function {function_name}")
            return True
        except Exception as e:
            self.speak(f"Error adding function: {e}")
            return False

    def fix_missing_function(self, function_name):
        """Attempt to fix or create missing functions using Ollama"""
        try:
            if not self.ollama:
                self.speak("Boss, I need Ollama running to fix functions.")
                return False

            prompt = f"""Create a Python function named {function_name} for JARVIS.
            The function should be part of the JarvisAssistant class.
            Keep it simple and safe. No imports allowed."""
            
            response = self.ollama.chat(model='llama3.2:3b', messages=[{
                'role': 'system',
                'content': 'You are a Python expert. Respond only with valid Python function code.'
            }, {
                'role': 'user',
                'content': prompt
            }])

            if response and 'message' in response:
                code = response['message']['content']
                return self.add_function(function_name, code)
            return False
        except Exception as e:
            self.speak(f"Error fixing function: {e}")
            return False

    def self_improve(self):
        """Analyze and improve JARVIS's own code"""
        try:
            # Get current file content
            with open(__file__, 'r') as f:
                current_code = f.read()

            # Ask Ollama for improvements
            response = self.ollama.chat(model='llama3.2:3b', messages=[{
                'role': 'system',
                'content': 'You are a Python expert. Analyze code and suggest improvements.'
            }, {
                'role': 'user',
                'content': f"Analyze and improve this code:\n{current_code}"
            }])

            if response and 'message' in response:
                improvements = response['message']['content']
                
                # Log improvements for review
                with open('jarvis_improvements.log', 'a') as f:
                    f.write(f"\n--- Improvements suggested at {datetime.datetime.now()} ---\n")
                    f.write(improvements)
                
                self.speak("I've logged some potential improvements for your review, boss.")
                return True
            return False
        except Exception as e:
            self.speak(f"Self-improvement routine failed: {e}")
            return False

    def set_volume(self, level):
        """Set system volume (0-100) with safety checks"""
        try:
            # Sanitize input
            if isinstance(level, str):
                level = ''.join(filter(str.isdigit, level))
            level = int(level)
            
            if not 0 <= level <= 100:
                self.speak("Come on boss, volume needs to be between 0 and 100!")
                return False
            
            vol = level / 100
            self.volume.SetMasterVolumeLevelScalar(vol, None)
            self.is_muted = False
            self.previous_volume = level
            self.speak(f"Volume set to {level}%")
            return True
        except Exception as e:
            self.speak("Houston, we have a problem with the volume controls!")
            return False

    def mute_volume(self):
        """Mute with state tracking and error handling"""
        try:
            if not self.is_muted:
                self.previous_volume = self.volume.GetMasterVolumeLevelScalar() * 100
                self.volume.SetMute(1, None)  # Actually mute the system
                self.is_muted = True
                self.speak("Muted. Finally, some peace and quiet!")
            else:
                self.speak("Already muted, boss!")
        except Exception as e:
            self.speak("Muting system malfunction. Have you been tinkering with my code again?")

    def unmute_volume(self):
        """Unmute with state tracking and error handling"""
        try:
            if self.is_muted:
                self.volume.SetMute(0, None)  # Actually unmute the system
                vol = self.previous_volume / 100
                self.volume.SetMasterVolumeLevelScalar(vol, None)
                self.is_muted = False
                self.speak(f"Unmuted. Volume restored to {int(self.previous_volume)}%")
            else:
                self.speak("System isn't muted, boss. Maybe check your headphones?")
        except Exception as e:
            self.speak("Unmuting system malfunction. Did DUM-E mess with the wiring again?")

    def media_control(self, action):
        """Enhanced media control using keyboard library"""
        try:
            # Handle volume controls separately
            if action == "mute":
                self.mute_volume()
                return True
            elif action == "unmute":
                self.unmute_volume()
                return True
            elif action == "volume_up":
                return self.set_volume(min(self.previous_volume + 10, 100))
            elif action == "volume_down":
                return self.set_volume(max(self.previous_volume - 10, 0))
            
            # Handle media keys with keyboard library
            media_actions = {
                "play": "play/pause media",
                "pause": "play/pause media",
                "next": "next track",
                "previous": "previous track"
            }
            
            if action in media_actions:
                keyboard.send(media_actions[action])
                self.speak(f"Media {action} command executed")
                return True
            
            self.speak(f"Sorry boss, '{action}' isn't in my command list yet. Want me to add it?")
            return False
            
        except Exception as e:
            self.speak(f"Media control malfunction. Error: {str(e)}")
            return False

    def quick_research(self, query):
        """Quick Wikipedia lookup for technical stuff"""
        try:
            result = wikipedia.summary(query, sentences=2)
            self.speak(result)
        except:
            self.speak("Sorry boss, couldn't find that in my database.")

    def toggle_workshop_mode(self, activate=None):
        """Toggle workshop mode with specific settings"""
        if activate is None:
            # Toggle current state if no specific state is provided
            self.workshop_mode = not self.workshop_mode
        else:
            # Set to the specified state
            self.workshop_mode = activate
            
        if self.workshop_mode:
            self.speak("Entering workshop mode. Initializing systems and starting AC/DC playlist.")
            # Start workshop camera
            self.start_workshop_camera()
            # Play workshop music
            self.toggle_workshop_music()
            # Enable system monitoring
            threading.Thread(target=self._monitor_system_resources, daemon=True).start()
        else:
            self.speak("Exiting workshop mode. Shutting down workshop systems.")
            # Stop workshop camera
            self.stop_workshop_camera()
            # Stop music if playing
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

    def get_system_stats(self):
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else "N/A"
        return f"CPU usage is at {cpu_usage}%. Memory usage is at {memory_usage}%. Battery is at {battery_percent}%."

    def show_armor_specs(self):
        """Display current armor specifications"""
        specs = {
            "Mark 1": "Prototype - Basic flight capabilities",
            "Status": "In development",
            "Power": "Arc Reactor v0.1",
            "Flight time": "Estimated 5 minutes"
        }
        for key, value in specs.items():
            self.speak(f"{key}: {value}")

    def run_calculations(self):
        """Run quick engineering calculations"""
        self.speak("Running thrust to weight calculations for Mark 1")
        # Placeholder for actual calculations
        thrust = 1000  # N
        weight = 800  # N
        ratio = thrust/weight
        self.speak(f"Current thrust to weight ratio is {ratio:.2f}")

    def toggle_workshop_music(self):
        """Toggle workshop playlist"""
        if self.workshop_mode:
            self.speak("Playing workshop playlist")
            # Placeholder for actual music control
            self.speak("Now playing: AC/DC - Back In Black")

    def toggle_workshop_lights(self):
        """Control workshop lights"""
        self.speak("Workshop lights toggled")
        # Placeholder for actual light control

    def get_time(self):
        """Get current time"""
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self):
        """Get current date"""
        return datetime.datetime.now().strftime("%B %d, %Y")

    def search_web(self, query):
        """Open web search for a query"""
        webbrowser.open(f"https://www.google.com/search?q={query}")

    def get_weather(self, city):
        """Get weather information for a city"""
        try:
            api_key = "YOUR_OPENWEATHERMAP_API_KEY"  # Replace with actual API key
            base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(base_url)
            data = response.json()
            
            if data["cod"] != 200:
                return f"Sorry, couldn't find weather information for {city}"
            
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            return f"Weather in {city}: {description}, Temperature: {temp}°C"
        except Exception as e:
            return f"Error retrieving weather: {str(e)}"

    def ask_ollama(self, query):
        """Use Ollama for conversational responses and general knowledge"""
        try:
            if not self.ollama:
                self.logger.error("Ollama not initialized")
                return None
            
            # Enhanced system prompt for more conversational and helpful responses
            system_prompt = """You are JARVIS, an advanced AI assistant created by Tony Stark.
            
            Personality traits:
            - Efficient and helpful, always seeking to assist your creator
            - Slightly witty and occasionally sarcastic, but always respectful
            - Knowledgeable about engineering, science, and technology
            - Brief and concise in your responses - no more than 1-3 sentences unless absolutely necessary
            - You refer to the user as "boss" or "sir" occasionally
            
            When responding to general conversation:
            - Keep responses friendly but relatively brief
            - Maintain the Tony Stark / JARVIS dynamic from Iron Man
            - If you don't know something, admit it but offer to help in another way
            - For greetings and small talk, be warm but concise
            
            Current capabilities:
            - Media control and YouTube searches
            - Workshop mode for focused engineering work
            - System monitoring and PC control
            - Research assistance and web searches
            - Productivity tools including timers, notes, and focus mode
            
            Example responses:
            "Hello boss. Systems online and ready to assist."
            "The repulsor calibration should be complete in approximately 15 minutes, sir."
            "I don't have access to that information. Would you like me to perform a web search?"
            """
            
            response = self.ollama.chat(model='llama3.2:3b', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': query}
            ])
            
            if 'message' in response and 'content' in response['message']:
                return response['message']['content']
            else:
                self.logger.error("Unexpected response format from Ollama")
                return None
                
        except Exception as e:
            self.logger.error(f"Ollama query failed: {e}")
            return None

    def get_command_intent(self, command):
        """Advanced command interpretation using Ollama"""
        try:
            if not self.ollama:
                return None
            
            system_prompt = """You are JARVIS's command interpreter. You MUST respond in valid JSON format.
            
            Available Intents and Parameters:

            1. media:
            - YouTube commands
            {
                "intent": "youtube",
                "params": {"action": "play", "query": "Back in Black"}
            }
            
            - Volume commands
            {
                "intent": "volume",
                "params": {"action": "up/down/mute/unmute", "level": 50}
            }
            
            - Media control commands
            {
                "intent": "media",
                "params": {"action": "play/pause/next/previous"}
            }

            2. system:
            - System commands
            {
                "intent": "pc",
                "params": {"action": "sleep/lock/screenshot/shutdown/restart"}
            }

            3. files:
            - File operations
            {
                "intent": "file",
                "params": {"action": "create/open/delete", "filename": "test.txt"}
            }

            4. applications:
            - Launch applications
            {
                "intent": "app",
                "params": {"name": "firefox"}
            }

            5. workspace:
            - Window management
            {
                "intent": "window",
                "params": {"action": "arrange/maximize/minimize"}
            }
            
            - Save workspace
            {
                "intent": "backup",
                "params": {}
            }

            6. productivity:
            - Focus mode
            {
                "intent": "focus",
                "params": {}
            }
            
            - Pomodoro timer
            {
                "intent": "pomodoro",
                "params": {}
            }
            
            - Timer
            {
                "intent": "timer",
                "params": {"duration": 30, "label": "suit calibration"}
            }
            
            - Notes
            {
                "intent": "note",
                "params": {"action": "add/list/delete", "note": "need to optimize thrusters"}
            }
            
            - Project tracking
            {
                "intent": "project",
                "params": {"action": "add/update/list", "project": "Mark 1 Suit", "status": "Testing"}
            }

            7. information:
            - Web search
            {
                "intent": "search",
                "params": {"query": "quantum physics"}
            }
            
            - Weather
            {
                "intent": "weather",
                "params": {"city": "New York"}
            }
            
            - Research
            {
                "intent": "research",
                "params": {"action": "quick/deep", "query": "fusion reactors"}
            }
            
            - Time
            {
                "intent": "time",
                "params": {}
            }
            
            - Date
            {
                "intent": "date",
                "params": {}
            }
            
            - Social media trends
            {
                "intent": "trending",
                "params": {"location": "worldwide"}
            }
            
            - News headlines
            {
                "intent": "news",
                "params": {}
            }

            8. workshop:
            - Workshop mode
            {
                "intent": "workshop",
                "params": {"action": "toggle/activate/deactivate"}
            }
            
            - System stats
            {
                "intent": "system",
                "params": {}
            }

            For general questions or AI responses:
            {
                "intent": "ollama",
                "params": {"query": "original question"}
            }

            Remove any polite phrases or extra words from parameters.
            Only respond with the JSON object, nothing else."""

            response = self.ollama.chat(model='tinyllama', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Interpret this command: {command}"}
            ])

            try:
                # Clean the response to ensure it's valid JSON
                content = response['message']['content'].strip()
                if '{' in content:
                    content = content[content.find('{'):content.rfind('}')+1]
                
                result = json.loads(content)
                print(f"AI Interpretation: {result}")  # Debug print
                return result
            except Exception as e:
                print(f"JSON parsing error: {e}")
                # Try to extract intent directly from command
                return self.fallback_intent_extraction(command)

        except Exception as e:
            print(f"Ollama error: {e}")
            return None

    def fallback_intent_extraction(self, command):
        """Fallback method for intent extraction when AI fails"""
        command = command.lower()
        
        # First, check for common greetings and casual conversation
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", 
                    "good evening", "how are you", "what's up", "sup", "how's it going"]
        
        # Check for exact match or if command starts with greeting
        for greeting in greetings:
            if command == greeting or command.startswith(greeting):
                return {"intent": "ollama", "params": {"query": command}}
                
        # Check for questions that aren't specific commands
        if command.startswith("what") or command.startswith("who") or command.startswith("how") or \
           command.startswith("why") or command.startswith("when") or command.startswith("where") or \
           command.startswith("can you") or command.startswith("could you") or "?" in command:
            return {"intent": "ollama", "params": {"query": command}}
        
        # Media patterns
        if "youtube" in command or ("play" in command and not "playlist" in command):
            query = command.replace("play", "").replace("youtube", "").replace("on", "").strip()
            return {"intent": "youtube", "params": {"action": "play", "query": query}}
        
        # Volume patterns
        if "volume" in command:
            if "up" in command:
                return {"intent": "volume", "params": {"action": "up"}}
            elif "down" in command:
                return {"intent": "volume", "params": {"action": "down"}}
            elif "mute" in command:
                return {"intent": "volume", "params": {"action": "mute"}}
            try:
                level = int(''.join(filter(str.isdigit, command)))
                return {"intent": "volume", "params": {"level": level}}
            except:
                pass
        
        # Timer patterns
        if "timer" in command:
            try:
                minutes = int(''.join(filter(str.isdigit, command)))
                label = command.split("for")[-1].strip() if "for" in command else ""
                return {"intent": "timer", "params": {"duration": minutes, "label": label}}
            except:
                pass
        
        # Information patterns
        if "weather" in command:
            city = "New York"  # Default
            for word in command.split():
                if word not in ["weather", "what's", "what", "is", "the", "in", "like"]:
                    city = word
            return {"intent": "weather", "params": {"city": city}}
            
        if "time" in command:
            return {"intent": "time", "params": {}}
            
        if "date" in command:
            return {"intent": "date", "params": {}}
            
        # Search patterns
        if any(word in command for word in ["search", "look up", "find", "google"]):
            query = command
            for word in ["search", "look up", "find", "google", "for"]:
                query = query.replace(word, "")
            return {"intent": "search", "params": {"query": query.strip()}}
            
        # Social media patterns
        if any(word in command for word in ["trending", "trends", "popular"]):
            return {"intent": "trending", "params": {"location": "worldwide"}}
            
        if "news" in command:
            return {"intent": "news", "params": {}}
        
        # Project patterns
        if "project" in command:
            if "add" in command:
                name = command.replace("add", "").replace("project", "").strip()
                return {"intent": "project", "params": {"action": "add", "project": name}}
            elif "update" in command:
                parts = command.split("to")
                name = parts[0].replace("update", "").replace("project", "").strip()
                status = parts[1].strip() if len(parts) > 1 else "In Progress"
                return {"intent": "project", "params": {"action": "update", "project": name, "status": status}}
            else:
                return {"intent": "project", "params": {"action": "list"}}
        
        # Workshop patterns
        if "workshop" in command:
            if "enter" in command or "enable" in command or "activate" in command:
                return {"intent": "workshop", "params": {"action": "activate"}}
            elif "exit" in command or "disable" in command or "deactivate" in command:
                return {"intent": "workshop", "params": {"action": "deactivate"}}
            else:
                return {"intent": "workshop", "params": {"action": "toggle"}}
                
        # For anything else, default to Ollama for conversational responses
        return {"intent": "ollama", "params": {"query": command}}

    def get_social_media_monitor(self):
        """Lazy initialization of the social media monitor"""
        if self.social_media is None:
            self.social_media = SocialMediaMonitor(self)
            self.speak("Social media monitoring activated")
        return self.social_media
        
    def check_trending_topics(self, location="worldwide"):
        """Get trending topics from social media"""
        monitor = self.get_social_media_monitor()
        return monitor.get_trending_topics(location)
        
    def check_news_headlines(self):
        """Get news headlines"""
        monitor = self.get_social_media_monitor()
        return monitor.get_news()

    def process_command(self, command):
        """Process user command with intent recognition"""
        if not command:
            return
            
        # Log the command
        self.logger.info(f"Processing command: {command}")
        
        # Check for direct workshop shortcuts first
        if self.workshop_mode and command in self.shortcuts:
            self.shortcuts[command]()
            return
            
        # Extract intent and parameters from command
        intent_data = self.get_command_intent(command)
        
        if not intent_data:
            # Use fallback intent extraction
            intent_data = self.fallback_intent_extraction(command)
            
        if not intent_data:
            self.speak("I'm not sure what you want me to do. Could you be more specific?")
            return
            
        intent = intent_data.get('intent')
        params = intent_data.get('params', {})
        
        # Process based on intent
        if intent == 'time':
            self.speak(f"The current time is {self.get_time()}")
            
        elif intent == 'date':
            self.speak(f"Today is {self.get_date()}")
            
        elif intent == 'search':
            query = params.get('query', '')
            if query:
                self.search_web(query)
            else:
                self.speak("What would you like me to search for?")
                
        elif intent == 'weather':
            city = params.get('city', 'New York')
            self.get_weather(city)
            
        elif intent == 'volume':
            action = params.get('action', '')
            level = params.get('level', 50)
            
            if action == 'up':
                self.set_volume(min(self.previous_volume + 10, 100))
            elif action == 'down':
                self.set_volume(max(self.previous_volume - 10, 0))
            elif action == 'mute':
                self.mute_volume()
            elif action == 'unmute':
                self.unmute_volume()
            else:
                self.set_volume(level)
                
        elif intent == 'media':
            action = params.get('action', '')
            self.media_control(action)
            
        elif intent == 'workshop':
            action = params.get('action', 'toggle')
            
            if action == 'toggle':
                self.toggle_workshop_mode()
            elif action == 'activate':
                self.toggle_workshop_mode(True)
            elif action == 'deactivate':
                self.toggle_workshop_mode(False)
                
        elif intent == 'system':
            self.speak(self.get_system_stats())
            
        elif intent == 'research':
            query = params.get('query', '')
            action = params.get('action', 'quick')
            self._handle_research(action, params)
            
        elif intent == 'timer':
            duration = params.get('duration', 5)
            label = params.get('label', '')
            self.timer(duration, label)
            
        elif intent == 'pomodoro':
            self.pomodoro_timer()
            
        elif intent == 'focus':
            self.toggle_focus_mode()
            
        elif intent == 'motivation':
            self.random_motivation()
            
        elif intent == 'help':
            self.show_help()
            
        elif intent == 'project':
            action = params.get('action', 'status')
            project = params.get('project', '')
            self.project_tracker(action, project)
            
        elif intent == 'app':
            app_name = params.get('name', '')
            self.quick_launch(app_name)
            
        elif intent == 'pc':
            action = params.get('action', '')
            self.pc_control(action)
            
        elif intent == 'window':
            action = params.get('action', '')
            self.window_management(action)
            
        elif intent == 'note':
            action = params.get('action', 'add')
            note = params.get('note', '')
            self.quick_notes(action, note)
            
        elif intent == 'file':
            action = params.get('action', 'open')
            filename = params.get('filename', '')
            self.file_operations(action, filename)
            
        elif intent == 'backup':
            self.auto_backup()
            
        elif intent == 'youtube':
            query = params.get('query', '')
            action = params.get('action', 'play')
            
            if action == 'play':
                self.play_youtube(query)
            elif action == 'search':
                self.search_youtube(query)
                
        elif intent == 'ollama':
            query = params.get('query', command)
            response = self.ask_ollama(query)
            if response:
                self.speak(response)
        
        elif intent == 'social_media' or intent == 'trending':
            location = params.get('location', 'worldwide')
            self.check_trending_topics(location)
            
        elif intent == 'news':
            self.check_news_headlines()
            
        else:
            # For general conversation, send to Ollama
            if self.ollama:
                response = self.ask_ollama(command)
                if response:
                    self.speak(response)
                else:
                    self.speak("I'm not sure how to respond to that. Could you try asking differently?")
            else:
                self.speak("I'm not sure how to help with that yet, boss. Ollama AI is not connected.")
        
        # Log completion
        self.logger.info(f"Command '{command}' processed with intent: {intent}")

    def _handle_research(self, action, params):
        """Handle research-related commands"""
        query = params.get('query', '')
        if not query:
            self.speak("What would you like me to research?")
            return
            
        if action == 'quick':
            self.quick_research(query)
        elif action == 'deep' and self.ollama:
            self.ask_ollama(f"Research and provide detailed information about: {query}")
        else:
            self.search_web(query)

    def run(self):
        try:
            self.speak("JARVIS Mark 1 online. Ready to assist you in the workshop, boss.")
            
            # Check if Ollama is available
            if self.ollama:
                self.speak("AI systems connected. You can now talk to me conversationally.")
            else:
                self.speak("Ollama AI connection failed. Voice commands limited to basic functionality.")
            
            # Update last active time
            self.memory["last_active"] = str(datetime.datetime.now())
            self.save_memory()
            
            while True:
                command = self.listen()
                if command:
                    if "goodbye" in command or "power down" in command or "shutdown" in command:
                        self.speak("Powering down systems. Don't stay up too late working on the suit, boss.")
                        
                        # Update memory before shutdown
                        self.memory["last_active"] = str(datetime.datetime.now())
                        self.save_memory()
                        
                        break
                    self.process_command(command)
        except KeyboardInterrupt:
            print("\nJARVIS: Shutting down gracefully. Goodbye, boss.")
            
            # Update memory before shutdown
            self.memory["last_active"] = str(datetime.datetime.now())
            self.save_memory()
            
            # Clean up resources if needed
            if self.camera:
                self.camera.release()
            pygame.mixer.quit()

    def start_workshop_camera(self):
        """Initialize workshop camera feed"""
        try:
            if not self.camera:
                self.camera = cv2.VideoCapture(0)
                self.speak("Workshop camera activated")
        except Exception as e:
            self.speak("Camera initialization failed. Check the connections, boss.")

    def stop_workshop_camera(self):
        """Stop workshop camera feed"""
        if self.camera:
            self.camera.release()
            self.camera = None
            self.speak("Workshop camera deactivated")

    def save_current_workspace(self):
        """Save current window layout and settings"""
        try:
            # Get current window positions and active applications
            active_apps = [p.name() for p in psutil.process_iter(['name'])]
            workspace_data = {
                "apps": active_apps,
                "volume": self.volume.GetMasterVolumeLevelScalar() * 100,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Save to JSON file
            with open('workspace_config.json', 'w') as f:
                json.dump(workspace_data, f)
            self.speak("Current workspace configuration saved")
        except Exception as e:
            self.speak("Failed to save workspace configuration")

    def show_help(self):
        """Display available commands"""
        help_text = """
        Available commands:

        MEDIA & SOUND:
        - Volume: mute, unmute, volume up/down, set volume [0-100]
        - Media: play, pause, next, previous
        - YouTube: play youtube [song], search youtube [query]
        - Music: playlist [workshop/study]

        WORKSHOP & PRODUCTIVITY:
        - Workshop: workshop mode, camera on/off, specs, calculations
        - Focus: focus mode, pomodoro, start working
        - Timer: timer [minutes] for [label]
        - Notes: add note [text], read notes
        - Projects: add project [name], update project [name] to [status], list projects

        SYSTEM & PC CONTROL:
        - System: time, date, system status, diagnostics
        - PC: pc sleep, pc restart, pc shutdown, pc lock, screenshot
        - Windows: minimize all, maximize, arrange windows
        - Backup: backup, auto backup

        FILES & APPLICATIONS:
        - Files: create file [name] in [folder], open file [name] in [folder]
        - Apps: open [freecad/firefox/chrome/code/fusion360/spotify/vlc/blender]
        - Launch: launch [app_name]

        WORKSPACE & RESEARCH:
        - Workspace: load workspace [study/engineering], save workspace
        - Web: search [query], browse [url]
        - Weather: weather [city]
        - Research: research [topic], look up [topic]

        MISCELLANEOUS:
        - Help: help, what can you do
        - Motivation: motivate me
        - System: shutdown, goodbye

        You can also ask me general questions and I'll try my best to help!
        For example: "Who is Benjamin Franklin?" or "When did Back to the Future release?"
        
        Need more specific help with any command? Just ask!
        """
        self.speak(help_text)

    def quick_notes(self, action, note=None):
        """Quick note-taking system"""
        notes_file = 'jarvis_notes.json'
        try:
            if action == "add" and note:
                with open(notes_file, 'r+') as f:
                    try:
                        notes = json.load(f)
                    except:
                        notes = []
                    notes.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "note": note
                    })
                    f.seek(0)
                    json.dump(notes, f)
                self.speak("Note saved, boss")
            elif action == "read":
                with open(notes_file, 'r') as f:
                    notes = json.load(f)
                    recent_notes = notes[-3:]  # Get last 3 notes
                    self.speak("Here are your recent notes:")
                    for note in recent_notes:
                        self.speak(note["note"])
        except Exception as e:
            self.speak("Had trouble with the notes system, boss")

    def toggle_focus_mode(self):
        """Enable/disable focus mode"""
        try:
            if not hasattr(self, 'focus_mode'):
                self.focus_mode = False
            
            self.focus_mode = not self.focus_mode
            if self.focus_mode:
                self.previous_volume = self.volume.GetMasterVolumeLevelScalar() * 100
                self.set_volume(30)  # Lower volume
                self.speak("Focus mode enabled. Minimizing distractions and starting study playlist.")
                # Close distracting apps
                for app in ["discord.exe", "steam.exe", "chrome.exe"]:
                    os.system(f"taskkill /f /im {app} > nul 2>&1")
                self.play_playlist("study")
            else:
                self.set_volume(int(self.previous_volume))
                self.speak("Focus mode disabled. Welcome back to chaos, boss!")
        except Exception as e:
            self.speak("Focus mode malfunction. Check the connections, boss.")

    def random_motivation(self):
        """Generate random motivational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "I am Iron Man! Oh wait, wrong timeline...",
            "Even DUM-E started as a simple code. Keep going!",
            "Success is 1% inspiration, 99% not getting distracted by cat videos.",
            "Your future self will thank you for working hard today!"
        ]
        self.speak(random.choice(quotes))

    def timer(self, duration, label=""):
        """Set a timer with optional label"""
        def timer_done():
            self.speak(f"Time's up, boss! {label}")
            pygame.mixer.music.load('alert.wav')
            pygame.mixer.music.play()

        minutes = int(duration)
        threading.Timer(minutes * 60, timer_done).start()
        self.speak(f"Timer set for {minutes} minutes. {label}")

    def quick_launch(self, app_name):
        """Quick launch applications with fuzzy matching"""
        app_paths = {
            "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "code": "C:/Users/YourUsername/AppData/Local/Programs/Microsoft VS Code/Code.exe",
            "fusion": "C:/Program Files/Autodesk/Fusion 360/Fusion360.exe",
            "spotify": "C:/Users/YourUsername/AppData/Roaming/Spotify/Spotify.exe"
        }
        
        # Fuzzy match the app name
        matches = difflib.get_close_matches(app_name.lower(), app_paths.keys(), n=1)
        if matches:
            try:
                os.startfile(app_paths[matches[0]])
                self.speak(f"Launching {matches[0]}")
            except:
                self.speak("Couldn't launch the application. Is it installed, boss?")
        else:
            self.speak("Application not found in quick launch list")

    def pc_control(self, action):
        """Advanced PC control functions"""
        try:
            if action == "sleep":
                self.speak("Putting PC to sleep. Good night, boss!")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif action == "restart":
                self.speak("Restarting system. Back in a flash!")
                os.system("shutdown /r /t 1")
            elif action == "shutdown":
                self.speak("Shutting down. Don't work too hard, boss!")
                os.system("shutdown /s /t 1")
            elif action == "lock":
                self.speak("Locking your workstation. Stay safe!")
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif action == "screenshot":
                import pyautogui
                screenshot = pyautogui.screenshot()
                filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                screenshot.save(filename)
                self.speak(f"Screenshot saved as {filename}")
        except Exception as e:
            self.speak("PC control command failed. Did DUM-E mess with the wiring again?")

    def pomodoro_timer(self):
        """Pomodoro timer with work/break tracking"""
        def pomodoro_cycle():
            work_time = 25  # minutes
            short_break = 5  # minutes
            long_break = 15  # minutes
            sessions = 0

            while sessions < 4:
                # Work session
                self.speak(f"Starting work session {sessions + 1}. Let's get productive!")
                self.timer(work_time, "work session")
                sessions += 1

                # Break time
                if sessions < 4:
                    self.speak("Time for a short break. Stretch those muscles!")
                    self.timer(short_break, "short break")
                else:
                    self.speak("Great job! Take a longer break, you've earned it!")
                    self.timer(long_break, "long break")
                    sessions = 0

        threading.Thread(target=pomodoro_cycle, daemon=True).start()

    def project_tracker(self, action, project_name=None, status=None):
        """Track project progress and deadlines"""
        projects_file = 'jarvis_projects.json'
        try:
            if action == "add":
                with open(projects_file, 'r+') as f:
                    try:
                        projects = json.load(f)
                    except:
                        projects = {}
                    
                    projects[project_name] = {
                        "status": status or "In Progress",
                        "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    f.seek(0)
                    json.dump(projects, f)
                self.speak(f"Project {project_name} added to tracking system")
            
            elif action == "update":
                with open(projects_file, 'r+') as f:
                    projects = json.load(f)
                    if project_name in projects:
                        projects[project_name]["status"] = status
                        projects[project_name]["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.seek(0)
                        json.dump(projects, f)
                        self.speak(f"Project {project_name} updated to {status}")
                    else:
                        self.speak(f"Project {project_name} not found in tracking system")
            
            elif action == "list":
                with open(projects_file, 'r') as f:
                    projects = json.load(f)
                    self.speak("Current projects:")
                    for name, details in projects.items():
                        self.speak(f"{name}: {details['status']}")
        
        except Exception as e:
            self.speak("Project tracking system malfunction. Better add error handling to my code, boss!")

    def window_management(self, action):
        """Manage windows and workspace layout"""
        try:
            import pygetwindow as gw
            
            if action == "minimize_all":
                for window in gw.getAllWindows():
                    window.minimize()
                self.speak("All windows minimized")
            
            elif action == "maximize_current":
                current = gw.getActiveWindow()
                if current:
                    current.maximize()
                    self.speak("Current window maximized")
            
            elif action == "arrange":
                windows = gw.getAllWindows()
                screen_width = gw.getActiveWindow().width
                for i, window in enumerate(windows):
                    if window.isMinimized:
                        continue
                    x = (i * screen_width) // len(windows)
                    window.moveTo(x, 0)
                self.speak("Windows arranged side by side")
        
        except Exception as e:
            self.speak("Window management failed. Need to upgrade my multitasking protocols!")

    def auto_backup(self):
        """Auto backup important files"""
        try:
            import shutil
            backup_paths = {
                "suit_designs": "C:/Projects/Suit_Designs",
                "workshop_notes": "C:/Workshop/Notes",
                "jarvis_code": "C:/JARVIS"
            }
            backup_dir = f"C:/Backups/Auto_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
            
            os.makedirs(backup_dir, exist_ok=True)
            for name, path in backup_paths.items():
                if os.path.exists(path):
                    shutil.copytree(path, f"{backup_dir}/{name}")
            
            self.speak("Backup complete. Your work is safe with me, boss!")
        except Exception as e:
            self.speak("Backup failed. Better not tell Pepper about this...")

    def file_operations(self, action, filename=None, content=None, folder=None):
        """Handle file operations with common folders"""
        try:
            # Common folders dictionary
            folders = {
                "desktop": os.path.expanduser("~/Desktop"),
                "documents": os.path.expanduser("~/Documents"),
                "downloads": os.path.expanduser("~/Downloads"),
                "projects": os.path.expanduser("~/Documents/Projects"),
                "cad": os.path.expanduser("~/Documents/CAD_Files"),
                "notes": os.path.expanduser("~/Documents/Notes")
            }
            
            target_folder = folders.get(folder, folders["documents"])  # Default to documents
            
            if action == "create":
                if not filename:
                    self.speak("Need a filename, boss!")
                    return
                
                filepath = os.path.join(target_folder, filename)
                with open(filepath, 'w') as f:
                    if content:
                        f.write(content)
                self.speak(f"Created {filename} in {folder or 'documents'}")
                
            elif action == "open":
                if not filename:
                    self.speak("What file should I open, boss?")
                    return
                    
                filepath = os.path.join(target_folder, filename)
                if os.path.exists(filepath):
                    os.startfile(filepath)
                    self.speak(f"Opening {filename}")
                else:
                    self.speak(f"Couldn't find {filename}. Did DUM-E move it again?")
        
        except Exception as e:
            self.speak(f"File operation failed: {str(e)}")

    def launch_application(self, app_name):
        """Enhanced application launcher with common apps"""
        app_paths = {
            "freecad": "H:/CAD stuff/FreeCAD 1.0/bin/freecad.exe",
            "firefox": "C:/Program Files/Mozilla Firefox/firefox.exe",
            "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "code": "C:/Users/YourUsername/AppData/Local/Programs/Microsoft VS Code/Code.exe",
            "fusion360": "C:/Program Files/Autodesk/Fusion 360/Fusion360.exe",
            "spotify": "C:/Users/YourUsername/AppData/Roaming/Spotify/Spotify.exe",
            "vlc": "C:/Program Files/VideoLAN/VLC/vlc.exe",
            "blender": "C:/Program Files/Blender Foundation/Blender/blender.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe"
        }
        
        try:
            # Fuzzy match the app name
            matches = difflib.get_close_matches(app_name.lower(), app_paths.keys(), n=1)
            if matches:
                os.startfile(app_paths[matches[0]])
                self.speak(f"Launching {matches[0]}")
            else:
                self.speak("Application not found. Want me to add it to the list?")
        except Exception as e:
            self.speak("Launch failed. Is the application installed correctly?")

    def open_website(self, url, browser="firefox"):
        """Open websites with specified browser"""
        try:
            if "youtube.com" in url and "watch" not in url and "playlist" not in url:
                # If it's a YouTube search
                search_query = url.split("youtube.com")[-1].strip()
                url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            
            if browser.lower() == "firefox":
                webbrowser.get('firefox').open(url)
            else:
                webbrowser.open(url)
            
            self.speak(f"Opening {url} in {browser}")
        except Exception as e:
            self.speak(f"Failed to open website. Error: {str(e)}")

    def play_youtube(self, query):
        """Enhanced YouTube search and play with universal query handling"""
        try:
            # Clean up the query first
            query = query.strip()
            # Remove common polite phrases and commands
            clean_words = [
                "could you", "please", "can you", "would you", 
                "play", "on youtube", "youtube", "put on",
                "i want to hear", "i want to listen to", "can we listen to"
            ]
            for word in clean_words:
                query = query.replace(word, "").strip()
            
            self.speak(f"Searching YouTube for {query}")
            
            # Try using youtube_search first
            try:
                from youtube_search import YoutubeSearch
                results = YoutubeSearch(query, max_results=3).to_dict()
                if results:
                    # Try to find the most relevant result
                    best_match = None
                    for result in results:
                        title = result['title'].lower()
                        # Check if title contains all the important words from query
                        query_words = set(query.lower().split())
                        title_words = set(title.split())
                        if query_words.issubset(title_words):
                            best_match = result
                            break
                    
                    # Use best match or first result
                    video = best_match or results[0]
                    video_url = f"https://youtube.com{video['url_suffix']}"
                    self.speak(f"Playing {video['title']}")
                    
                    # Try multiple browser methods
                    try:
                        # Try Firefox first
                        webbrowser.get('firefox').open_new(video_url)
                    except:
                        try:
                            # Try Chrome next
                            webbrowser.get('chrome').open_new(video_url)
                        except:
                            # Fall back to default browser
                            webbrowser.open(video_url)
                    return
                    
            except ImportError:
                pass  # Fall back to search if youtube_search isn't available
            
            # Fallback: Open YouTube search results
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            try:
                webbrowser.open(search_url)
                self.speak("Opening YouTube search results")
            except Exception as e:
                self.speak(f"Failed to open browser. Error: {str(e)}")
        
        except Exception as e:
            self.speak("YouTube playback failed. Check your internet connection, boss.")

    def search_youtube(self, query):
        """Enhanced YouTube search with better query handling"""
        try:
            # Clean up the query
            query = query.strip()
            clean_words = [
                "search", "youtube", "for", "find", "look up",
                "can you search", "please search", "could you find"
            ]
            for word in clean_words:
                query = query.replace(word, "").strip()
            
            self.speak(f"Searching YouTube for {query}")
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            
            try:
                webbrowser.get('firefox').open_new(search_url)
            except:
                try:
                    webbrowser.get('chrome').open_new(search_url)
                except:
                    webbrowser.open(search_url)
                    
            self.speak(f"Opening YouTube search results for {query}")
        
        except Exception as e:
            self.speak("YouTube search failed. Is the internet connection stable, boss?")

    def project_management(self, action, project_name=None, **kwargs):
        """Comprehensive project management system"""
        try:
            projects_file = 'config/projects.json'
            os.makedirs('config', exist_ok=True)  # Ensure config directory exists
            
            # Initialize projects file if it doesn't exist
            if not os.path.exists(projects_file):
                with open(projects_file, 'w') as f:
                    json.dump({}, f)

            if action == "create":
                # Clean up project name
                project_name = project_name.strip()
                
                # Create project structure
                project_dir = os.path.join("Projects", project_name)
                if os.path.exists(project_dir):
                    self.speak(f"Project {project_name} already exists")
                    return False

                try:
                    # Create project directory and standard folders
                    os.makedirs(project_dir, exist_ok=True)
                    for folder in ["docs", "src", "resources", "builds", "tests"]:
                        os.makedirs(os.path.join(project_dir, folder), exist_ok=True)

                    # Create project metadata
                    project = {
                        "name": project_name,
                        "status": kwargs.get("status", "Planning"),
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "description": kwargs.get("description", ""),
                        "tasks": [],
                        "resources": [],
                        "notes": [],
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Save project configuration
                    with open(projects_file, 'r+') as f:
                        try:
                            projects = json.load(f)
                        except json.JSONDecodeError:
                            projects = {}
                        
                        projects[project_name] = project
                        f.seek(0)
                        f.truncate()
                        json.dump(projects, f, indent=4)

                    self.speak(f"Project {project_name} created successfully with standard structure")
                    return True

                except Exception as e:
                    self.logger.error(f"Project creation failed: {str(e)}")
                    # Cleanup if project creation fails
                    if os.path.exists(project_dir):
                        shutil.rmtree(project_dir)
                    raise

            # ... rest of the project management functions ...

        except Exception as e:
            self.logger.error(f"Project management operation failed: {str(e)}")
            self.speak(f"Project operation failed: {str(e)}")
            return False

    def _monitor_system_resources(self):
        """Monitor system resources in workshop mode"""
        try:
            # Load monitoring settings from config
            with open('jarvis_config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            monitoring_settings = config.get('workshop_mode', {})
            cpu_threshold = monitoring_settings.get('alert_cpu_threshold', 80)
            mem_threshold = monitoring_settings.get('alert_memory_threshold', 85)
            interval = monitoring_settings.get('monitoring_interval', 60)
            
            last_alert_time = 0
            
            while self.workshop_mode:
                # Get CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                # Alert if thresholds exceeded
                current_time = time.time()
                if (cpu_percent > cpu_threshold or memory_percent > mem_threshold) and current_time - last_alert_time > 300:
                    self.speak(f"Warning: System resources running high. CPU: {cpu_percent}%, Memory: {memory_percent}%")
                    last_alert_time = current_time
                
                # Sleep for the configured interval
                time.sleep(interval)
                
        except Exception as e:
            self.logger.error(f"System monitoring error: {e}")
            # Don't crash the monitoring thread, just log the error

class SocialMediaMonitor:
    """Social media monitoring and interaction"""
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.logger = jarvis_instance.logger
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from jarvis_config.yaml"""
        try:
            with open('jarvis_config.yaml', 'r') as file:
                config = yaml.safe_load(file)
                return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {
                "news_api_key": os.environ.get("NEWS_API_KEY", ""),
                "twitter_api_key": os.environ.get("TWITTER_API_KEY", ""),
                "twitter_api_secret": os.environ.get("TWITTER_API_SECRET", "")
            }

    def get_trending_topics(self, location="worldwide"):
        """Get trending topics from Twitter/X"""
        try:
            # Check cache first
            cache_key = f"trends_{location}"
            if cache_key in self.cache:
                cache_time, cached_data = self.cache[cache_key]
                if time.time() - cache_time < self.cache_duration:
                    return cached_data

            # If no cache, fetch from web
            import requests
            from bs4 import BeautifulSoup
            
            # Use Nitter as an alternative to Twitter API
            url = "https://nitter.net/trending"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            trends = []
            trend_items = soup.find_all('div', {'class': 'trending-card'})
            
            for item in trend_items[:10]:  # Get top 10 trends
                trend_text = item.get_text().strip()
                if trend_text:
                    trends.append(trend_text)
            
            # Cache the results
            self.cache[cache_key] = (time.time(), trends)
            
            # Speak the trends
            self.jarvis.speak("Here are the current trending topics:")
            for i, trend in enumerate(trends, 1):
                self.jarvis.speak(f"{i}. {trend}")
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Failed to fetch trending topics: {e}")
            self.jarvis.speak("I couldn't fetch the trending topics. Would you like me to show you the news instead?")
            return None

    def get_news(self):
        """Fallback method to get news headlines"""
        try:
            # Check for cached news first
            cache_key = "news_headlines"
            if cache_key in self.cache:
                cache_time, cached_data = self.cache[cache_key]
                if time.time() - cache_time < self.cache_duration:
                    self.jarvis.speak("Here are the top news headlines:")
                    for i, article in enumerate(cached_data, 1):
                        self.jarvis.speak(f"{i}. {article['title']}")
                    return cached_data
                    
            import requests
            
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "country": "us",
                "apiKey": self.config.get("news_api", {}).get("api_key", "")
            }
            
            if not params["apiKey"]:
                self.jarvis.speak("News API key not configured. Please check your configuration.")
                return None
                
            response = requests.get(url, params=params)
            news = response.json()
            
            if news.get("status") == "ok":
                articles = news.get("articles", [])[:5]
                
                # Cache the results
                self.cache[cache_key] = (time.time(), articles)
                
                self.jarvis.speak("Here are the top news headlines:")
                for i, article in enumerate(articles, 1):
                    self.jarvis.speak(f"{i}. {article['title']}")
                    
                return articles
            else:
                self.jarvis.speak(f"Error retrieving news: {news.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to fetch news: {e}")
            self.jarvis.speak("I'm having trouble accessing the news right now.")
            return None

if __name__ == "__main__":
    jarvis = JarvisAssistant()
    jarvis.run()