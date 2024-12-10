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

class SmithLogger:
    """Advanced logging system for SMITH"""
    def __init__(self):
        self.logger = logging.getLogger('SMITH')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for detailed logs
        fh = logging.FileHandler('smith_debug.log')
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

class SmithAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.speaker = pyttsx3.init()
        self.speaker.setProperty('rate', 180)  # Faster speech rate because I'm always in a hurry
        self.speaker.setProperty('voice', 'english+m3')
        pygame.mixer.init()
        
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
            "workshop": ["AC/DC - Back In Black", "Black Sabbath - Iron Man", "Led Zeppelin - Immigrant Song", "Gorillaz - Rhinestone Eyes", "Kendrik Lamar - u"],
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

        self.logger = SmithLogger()

        # Initialize function registry
        self.function_registry = {}
        # Enable self-improvement mode
        self.self_improvement_enabled = True

    def speak(self, text):
        print(f"SMITH: {text}")
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
                    return text.lower()
                except sr.WaitTimeoutError:
                    self.speak("Still listening, sir. Take your time.")
                    return self.listen()  # Recursively continue listening
                except sr.UnknownValueError:
                    self.speak("Could you repeat that? My audio processing isn't as good as it will be in Mark 2.")
                    return ""
                except sr.RequestError as e:
                    self.speak(f"Network issues. Error: {e}")
                    return ""
        except Exception as e:
            self.speak(f"Sorry sir, having some technical difficulties: {e}")
            return ""

    def add_function(self, function_name, code_string):
        """Dynamically add new functions to SMITH"""
        try:
            # Validate and clean the code
            if 'import' in code_string.lower():
                self.speak("Sorry sir, can't import modules dynamically for security reasons.")
                return False
            
            # Add the function to the class
            exec(code_string)
            function_object = locals()[function_name]
            setattr(SmithAssistant, function_name, function_object)
            
            self.speak(f"Successfully added function {function_name}")
            return True
        except Exception as e:
            self.speak(f"Error adding function: {e}")
            return False

    def fix_missing_function(self, function_name):
        """Attempt to fix or create missing functions using Ollama"""
        try:
            if not self.ollama:
                self.speak("Sir, I need Ollama running to fix functions.")
                return False

            prompt = f"""Create a Python function named {function_name} for SMITH.
            The function should be part of the SmithAssistant class.
            Keep it simple and safe. No imports allowed."""
            
            response = self.ollama.chat(model='tinyllama', messages=[{ # Default: llama3.2:1b-instruct-q5_0
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
        """Analyze and improve SMITH's own code"""
        try:
            # Get current file content
            with open(__file__, 'r') as f:
                current_code = f.read()

            # Ask Ollama for improvements
            response = self.ollama.chat(model='tinyllama', messages=[{ # Default: llama3.2:1b-instruct-q5_0
                'role': 'system',
                'content': 'You are a Python expert. Analyze code and suggest improvements.'
            }, {
                'role': 'user',
                'content': f"Analyze and improve this code:\n{current_code}"
            }])

            if response and 'message' in response:
                improvements = response['message']['content']
                
                # Log improvements for review
                with open('smith_improvements.log', 'a') as f:
                    f.write(f"\n--- Improvements suggested at {datetime.datetime.now()} ---\n")
                    f.write(improvements)
                
                self.speak("I've logged some potential improvements for your review, sir.")
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
                self.speak("Come on sir, volume needs to be between 0 and 100!")
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
                self.speak("Already muted, sir!")
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
                self.speak("System isn't muted, sir. Maybe check your headphones?")
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
            
            self.speak(f"Sorry sir, '{action}' isn't in my command list yet. Want me to add it?")
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
            self.speak("Sorry sir, couldn't find that in my database.")

    def toggle_workshop_mode(self):
        """Toggle workshop mode with specific settings"""
        self.workshop_mode = not self.workshop_mode
        if self.workshop_mode:
            self.speak("Entering workshop mode. Initializing systems and starting AC/DC playlist.")
            self.set_volume(70)  # Louder for workshop
            self.camera = cv2.VideoCapture(0)  # Start workshop camera
        else:
            self.speak("Exiting workshop mode. Powering down workshop systems.")
            self.set_volume(50)  # Normal volume
            if self.camera:
                self.camera.release()

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
        """Use Ollama as fallback for unknown commands"""
        try:
            if not self.ollama:
                return None
            
            response = self.ollama.chat(model='tinyllama', messages=[{ # Default: llama3.2:1b-instruct-q5_0
                'role': 'system',
                'content': 'You are SMITH, a helpful AI assistant created by young Tony Stark. Keep responses brief and witty.'
            }, {
                'role': 'user',
                'content': query
            }])
            
            return response['message']['content']
        except Exception as e:
            return None

    def get_command_intent(self, command):
        """Advanced command interpretation using Ollama"""
        try:
            if not self.ollama:
                return None, None, {}
            
            system_prompt = """You are SMITH's command interpreter. You MUST respond in valid JSON format.
            
            Available Functions and Response Formats:

            1. MEDIA:
            - YouTube: "play Back in Black on YouTube"
            {
                "category": "MEDIA",
                "action": "youtube",
                "parameters": {"type": "play", "query": "Back in Black"}
            }
            
            - Volume: "set volume to 50" / "mute" / "unmute"
            {
                "category": "MEDIA",
                "action": "volume_control",
                "parameters": {"action": "set", "level": 50}
            }
            
            - Media Controls: "pause music" / "next track"
            {
                "category": "MEDIA",
                "action": "media_control",
                "parameters": {"action": "pause"}
            }

            2. PC_CONTROL:
            - System: "put pc to sleep" / "lock computer" / "take screenshot"
            {
                "category": "PC_CONTROL",
                "action": "sleep/lock/screenshot",
                "parameters": {}
            }

            3. FILES:
            - File Operations: "create file test.txt in documents"
            {
                "category": "FILES",
                "action": "create/open",
                "parameters": {"filename": "test.txt", "folder": "documents"}
            }

            4. APPS:
            - Launch: "open freecad" / "launch firefox"
            {
                "category": "APPS",
                "action": "launch",
                "parameters": {"app_name": "freecad"}
            }

            5. WORKSPACE:
            - Management: "save workspace" / "arrange windows"
            {
                "category": "WORKSPACE",
                "action": "save/load/window",
                "parameters": {"type": "study", "action": "arrange"}
            }

            6. PRODUCTIVITY:
            - Focus: "enable focus mode" / "start pomodoro"
            {
                "category": "PRODUCTIVITY",
                "action": "focus_mode/pomodoro",
                "parameters": {}
            }
            
            - Timer: "set timer for 30 minutes for suit calibration"
            {
                "category": "PRODUCTIVITY",
                "action": "timer",
                "parameters": {"duration": 30, "label": "suit calibration"}
            }
            
            - Notes: "add note: need to optimize thrusters"
            {
                "category": "PRODUCTIVITY",
                "action": "notes",
                "parameters": {"action": "add", "content": "need to optimize thrusters"}
            }
            
            - Projects: "add project Mark 1 Suit" / "update project Mark 1 to Testing"
            {
                "category": "PRODUCTIVITY",
                "action": "project",
                "parameters": {"action": "add", "name": "Mark 1 Suit", "status": "Testing"}
            }

            7. RESEARCH:
            - Web: "search for quantum physics" / "what's the weather in New York"
            {
                "category": "RESEARCH",
                "action": "web_search/weather",
                "parameters": {"query": "quantum physics", "city": "New York"}
            }

            8. WORKSHOP:
            - Controls: "enter workshop mode" / "show armor specs"
            {
                "category": "WORKSHOP",
                "action": "mode/specs/calculations",
                "parameters": {"status": "enter"}
            }

            For general questions, use:
            {
                "category": "general_query",
                "action": "ask",
                "parameters": {"query": "original question"}
            }

            Remove any polite phrases or extra words from parameters.
            Only respond with the JSON object, nothing else."""

            response = self.ollama.chat(model='tinyllama', messages=[ # Default: llama3.2:1b-instruct-q5_0
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
                return result["category"], result["action"], result.get("parameters", {})
            except Exception as e:
                print(f"JSON parsing error: {e}")
                # Try to extract intent directly from command
                return self.fallback_intent_extraction(command)

        except Exception as e:
            print(f"Ollama error: {e}")
            return None, None, {}

    def fallback_intent_extraction(self, command):
        """Fallback method for intent extraction when AI fails"""
        command = command.lower()
        
        # Media patterns
        if "youtube" in command or ("play" in command and not "playlist" in command):
            query = command.replace("play", "").replace("youtube", "").replace("on", "").strip()
            return "MEDIA", "youtube", {"type": "play", "query": query}
        
        # Volume patterns
        if "volume" in command:
            try:
                level = int(''.join(filter(str.isdigit, command)))
                return "MEDIA", "volume_control", {"action": "set", "level": level}
            except:
                pass
        
        # Timer patterns
        if "timer" in command:
            try:
                minutes = int(''.join(filter(str.isdigit, command)))
                label = command.split("for")[-1].strip() if "for" in command else ""
                return "PRODUCTIVITY", "timer", {"duration": minutes, "label": label}
            except:
                pass
        
        # Project patterns
        if "project" in command:
            if "add" in command:
                name = command.replace("add", "").replace("project", "").strip()
                return "PRODUCTIVITY", "project", {"action": "add", "name": name}
            elif "update" in command:
                parts = command.split("to")
                name = parts[0].replace("update", "").replace("project", "").strip()
                status = parts[1].strip() if len(parts) > 1 else "In Progress"
                return "PRODUCTIVITY", "project", {"action": "update", "name": name, "status": status}
        
        return None, None, {}

    def process_command(self, command):
        """Enhanced command processing with AI understanding"""
        if not command:
            return

        # Get command intent from Ollama
        category, action, params = self.get_command_intent(command)
        print(f"Processing: category={category}, action={action}, params={params}")  # Debug print
        
        if category == "MEDIA" and action == "youtube":
            if params.get("type") == "play":
                self.play_youtube(params["query"])
                return
        
        # If no specific match or if Ollama failed, try legacy processing
        if not category:
            # Check for YouTube-related keywords
            if "youtube" in command.lower() or ("play" in command.lower() and any(song in command.lower() for song in ["back in black", "ac/dc"])):
                query = command.lower().replace("play", "").replace("youtube", "").replace("on", "").strip()
                self.play_youtube(query)
                return
        
        # Rest of the command processing...
        try:
            if category == "MEDIA":
                if action == "volume_control":
                    if "level" in params:
                        self.set_volume(params["level"])
                    elif params.get("action") == "mute":
                        self.mute_volume()
                    elif params.get("action") == "unmute":
                        self.unmute_volume()
                elif action == "youtube":
                    if params.get("type") == "play":
                        self.play_youtube(params["query"])
                    elif params.get("type") == "search":
                        self.search_youtube(params["query"])
                elif action == "media_control":
                    self.media_control(params["action"])

            elif category == "PC_CONTROL":
                self.pc_control(action)

            elif category == "FILES":
                self.file_operations(action, 
                                   filename=params.get("filename"),
                                   folder=params.get("folder"))

            elif category == "APPS":
                self.launch_application(params["app_name"])

            elif category == "WORKSPACE":
                if action == "save":
                    self.save_current_workspace()
                elif action == "load":
                    self.load_workspace(params["type"])
                elif action == "window":
                    self.window_management(params["action"])

            elif category == "PRODUCTIVITY":
                if action == "focus_mode":
                    self.toggle_focus_mode()
                elif action == "pomodoro":
                    self.pomodoro_timer()
                elif action == "timer":
                    self.timer(params["duration"], params.get("label", ""))
                elif action == "notes":
                    self.quick_notes(params["action"], params.get("content"))
                elif action == "project":
                    self.project_tracker(params["action"], 
                                       params.get("name"),
                                       params.get("status"))

            elif category == "RESEARCH":
                if action == "weather":
                    self.get_weather(params["city"])
                elif action == "web_search":
                    self.search_web(params["query"])
                elif action == "web_search/trending":
                    self.social_media.get_trending_topics()

            elif category == "general_query":
                if self.ollama:
                    response = self.ask_ollama(command)
                    if response:
                        self.speak(response)

            elif category == "EMAIL":
                if action == "check":
                    self.email_manager.check_emails()
                elif action == "summarize":
                    self.email_manager.summarize_emails()
                elif action == "read":
                    email_index = params.get("index", 1)
                    self.email_manager.read_email(email_index)

            if "add function" in command:
                function_name = command.split("add function")[-1].strip()
                self.speak(f"Ready to add function {function_name}. Please provide the code.")
                code = self.listen()  # Get the function code
                self.add_function(function_name, code)
                return

            if "fix function" in command:
                function_name = command.split("fix function")[-1].strip()
                self.fix_missing_function(function_name)
                return

            if "improve yourself" in command or "self improve" in command:
                self.speak("Initiating self-improvement protocols")
                self.self_improve()
                return

        except Exception as e:
            self.speak(f"I understood what you wanted, but had trouble executing it. Error: {str(e)}")
            # Fallback to legacy command processing
            self.legacy_process_command(command)

    def _handle_research(self, action, params):
        """Optimized research command handling"""
        if action == "web_search/trending":
            self.social_media.get_trending_topics()
        elif action == "weather":
            self.get_weather(params.get("city", "local"))

    def run(self):
        try:
            self.speak("SMITH Mark 1 online. Ready to assist you in the workshop, sir.")
            while True:
                command = self.listen()
                if command:
                    if "goodbye" in command or "power down" in command:
                        self.speak("Powering down systems. Don't stay up too late working on the suit, sir.")
                        break
                    self.process_command(command)
        except KeyboardInterrupt:
            print("\nSMITH: Shutting down gracefully. Goodbye, sir.")
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
            self.speak("Camera initialization failed. Check the connections, sir.")

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
        notes_file = 'smith_notes.json'
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
                self.speak("Note saved, sir.")
            elif action == "read":
                with open(notes_file, 'r') as f:
                    notes = json.load(f)
                    recent_notes = notes[-3:]  # Get last 3 notes
                    self.speak("Here are your recent notes:")
                    for note in recent_notes:
                        self.speak(note["note"])
        except Exception as e:
            self.speak("Had trouble with the notes system, sir.")

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
                self.speak("Focus mode disabled. Welcome back to chaos, sir!")
        except Exception as e:
            self.speak("Focus mode malfunction. Check the connections, sir.")

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
            self.speak(f"Time's up, sir! {label}")
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
                self.speak("Couldn't launch the application. Is it installed, sir?")
        else:
            self.speak("Application not found in quick launch list")

    def pc_control(self, action):
        """Advanced PC control functions"""
        try:
            if action == "sleep":
                self.speak("Putting PC to sleep. Good night, sir!")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif action == "restart":
                self.speak("Restarting system. Back in a flash!")
                os.system("shutdown /r /t 1")
            elif action == "shutdown":
                self.speak("Shutting down. Don't work too hard, sir!")
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
        projects_file = 'smith_projects.json'
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
            self.speak("Project tracking system malfunction. Better add error handling to my code, sir!")

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
                "suit_designs_windows": "C:/Projects/Suit_Designs",
                "workshop_notes_windows": "C:/Workshop/Notes",
                "suit_designs_linux": "~/Projects/Suit_Designs",
                "workshop_notes_linux": "~/Workshop/Notes",
                "smith_code_windows": "C:/SMITH",
                "smith_code_linux": "~/SMITH"
            }
            backup_dir = f"C:/Backups/Auto_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
            
            os.makedirs(backup_dir, exist_ok=True)
            for name, path in backup_paths.items():
                if os.path.exists(path):
                    shutil.copytree(path, f"{backup_dir}/{name}")
            
            self.speak("Backup complete. Your work is safe with me, sir!")
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
                    self.speak("Need a filename, sir!")
                    return
                
                filepath = os.path.join(target_folder, filename)
                with open(filepath, 'w') as f:
                    if content:
                        f.write(content)
                self.speak(f"Created {filename} in {folder or 'documents'}")
                
            elif action == "open":
                if not filename:
                    self.speak("What file should I open, sir?")
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
            "firefox_dev_edition": "C:/Program Files/Firefox Developer Edition/firefox.exe",
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
            self.speak("YouTube playback failed. Check your internet connection, sir.")

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
            self.speak("YouTube search failed. Is the internet connection stable, sir?")

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

class AutomationEngine:
    """Advanced task automation system"""
    def __init__(self, smith_instance):
        self.smith = smith_instance
        self.logger = smith_instance.logger
        self.tasks_file = 'config/automated_tasks.json'
        self.running_tasks = {}
        
        # Task scheduling
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Load saved tasks
        self.load_tasks()

    def add_task(self, name, trigger_type, actions, schedule=None):
        """Add automated task with multiple triggers and actions"""
        try:
            task = {
                "name": name,
                "trigger_type": trigger_type,  # time, event, condition
                "actions": actions,
                "schedule": schedule,
                "created": datetime.now().isoformat(),
                "last_run": None,
                "status": "active"
            }
            
            # Schedule the task based on trigger type
            if trigger_type == "time" and schedule:
                job = self.scheduler.add_job(
                    self.execute_task,
                    'cron',
                    **schedule,
                    args=[name, actions]
                )
                self.running_tasks[name] = job
            
            # Save task configuration
            self._save_tasks()
            
            self.smith.speak(f"Task {name} automated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to add task: {e}")
            self.smith.speak("Task automation failed")

    def execute_task(self, name, actions):
        """Execute a series of automated actions"""
        try:
            self.logger.info(f"Executing task: {name}")
            
            for action in actions:
                action_type = action["type"]
                params = action["parameters"]
                
                if action_type == "open_app":
                    self.smith.launch_application(params["app_name"])
                
                elif action_type == "workspace":
                    self.smith.workspace_manager.load(params["workspace_type"])
                
                elif action_type == "command":
                    self.smith.process_command(params["command"])
                
                elif action_type == "script":
                    self._run_script(params["script_path"], params.get("args", []))
                
                time.sleep(action.get("delay", 1))  # Delay between actions
            
            self._update_task_status(name, "completed")
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            self._update_task_status(name, "failed")

class EngineeringTools:
    """Engineering and development tools integration"""
    def __init__(self, smith_instance):
        self.smith = smith_instance
        self.logger = smith_instance.logger
        
        # Load engineering configurations
        self.load_configs()
        
        # Initialize CAD integration
        self.init_cad_integration()
        
        # Setup calculation engine
        self.calc_engine = self.setup_calculation_engine()

    def init_cad_integration(self):
        """Initialize CAD software integration"""
        try:
            # Support for multiple CAD systems
            self.cad_systems = {
                "freecad": {
                    "path": "path/to/freecad",
                    "api": self._load_freecad_api()
                },
                "fusion360": {
                    "path": "path/to/fusion360",
                    "api": self._load_fusion360_api()
                }
            }
        except Exception as e:
            self.logger.error(f"CAD integration failed: {e}")

    def engineering_calculation(self, calc_type, parameters):
        """Perform engineering calculations"""
        try:
            if calc_type == "stress":
                return self._calculate_stress(parameters)
            elif calc_type == "thermal":
                return self._calculate_thermal(parameters)
            elif calc_type == "fluid":
                return self._calculate_fluid_dynamics(parameters)
            else:
                raise ValueError(f"Unknown calculation type: {calc_type}")
        except Exception as e:
            self.logger.error(f"Calculation failed: {e}")
            return None

    def generate_technical_drawing(self, model_path, output_format="pdf"):
        """Generate technical drawings from 3D models"""
        try:
            # Load the 3D model
            model = self._load_3d_model(model_path)
            
            # Generate views
            views = self._generate_standard_views(model)
            
            # Add dimensions
            self._add_dimensions(views)
            
            # Export drawing
            output_path = self._export_drawing(views, output_format)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Drawing generation failed: {e}")
            return None

class DevOpsIntegration:
    """Development and Operations Integration"""
    def __init__(self, smith_instance):
        self.smith = smith_instance
        self.logger = smith_instance.logger
        
        # Initialize git integration
        self.git = self.init_git_integration()
        
        # Setup CI/CD monitoring
        self.ci_cd = self.init_ci_cd_monitoring()
        
        # Initialize docker integration
        self.docker = self.init_docker_integration()

    def deploy_project(self, project_name, environment="development"):
        """Handle project deployment"""
        try:
            # Get project configuration
            project = self.smith.project_manager.get_project(project_name)
            
            # Run pre-deployment checks
            if not self._run_deployment_checks(project):
                raise Exception("Pre-deployment checks failed")
            
            # Build docker container
            container_id = self._build_container(project)
            
            # Run tests
            if not self._run_tests(container_id):
                raise Exception("Tests failed")
            
            # Deploy
            self._deploy_container(container_id, environment)
            
            self.smith.speak(f"Project {project_name} deployed to {environment}")
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            self.smith.speak("Deployment failed")

    def monitor_services(self):
        """Monitor running services and containers"""
        try:
            # Check docker containers
            containers = self.docker.containers.list()
            
            # Check service health
            for container in containers:
                health = container.attrs['State']['Health']['Status']
                if health != 'healthy':
                    self.smith.speak(f"Warning: Container {container.name} is {health}")
            
            # Monitor resource usage
            self._check_resource_usage()
            
        except Exception as e:
            self.logger.error(f"Service monitoring failed: {e}")

class EmailManager:
    """Advanced email management system"""
    def __init__(self, smith_instance):
        self.smith = smith_instance
        self.logger = smith_instance.logger
        self.email_config_file = 'config/email_config.json'
        self.email_cache = {}
        self.last_check = None
        
        # Load email configuration
        self.load_config()
        
    def load_config(self):
        """Load email configuration"""
        try:
            with open(self.email_config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.smith.speak("Email configuration not found. Would you like to set up email integration?")
            # Could add interactive setup here
            self.config = {}

    def check_emails(self, folder="inbox"):
        """Check for new emails"""
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            # Connect to email server
            mail = imaplib.IMAP4_SSL(self.config.get('imap_server', 'imap.gmail.com'))
            mail.login(self.config['email'], self.config['password'])
            
            # Select folder
            mail.select(folder)
            
            # Search for unread emails
            _, messages = mail.search(None, 'UNSEEN')
            
            if not messages[0]:
                self.smith.speak("No new emails, sir.")
                return []
            
            new_emails = []
            for num in messages[0].split():
                _, msg = mail.fetch(num, '(RFC822)')
                email_body = msg[0][1]
                email_message = email.message_from_bytes(email_body)
                
                subject = decode_header(email_message["Subject"])[0][0]
                sender = decode_header(email_message.get("From"))[0][0]
                
                if isinstance(subject, bytes):
                    subject = subject.decode()
                if isinstance(sender, bytes):
                    sender = sender.decode()
                
                new_emails.append({
                    "subject": subject,
                    "sender": sender,
                    "id": num,
                    "full_message": email_message
                })
            
            count = len(new_emails)
            self.smith.speak(f"You have {count} new {'email' if count == 1 else 'emails'}")
            
            # Cache the results
            self.email_cache = {
                'timestamp': datetime.now(),
                'emails': new_emails
            }
            
            return new_emails
            
        except Exception as e:
            self.logger.error(f"Email check failed: {e}")
            self.smith.speak("Unable to check emails. Please verify your email configuration.")
            return []

    def summarize_emails(self, emails=None):
        """Summarize emails for voice output"""
        try:
            if emails is None:
                if not self.email_cache:
                    emails = self.check_emails()
                else:
                    emails = self.email_cache['emails']
            
            if not emails:
                return
            
            self.smith.speak("Here's a summary of your new emails:")
            for i, email in enumerate(emails, 1):
                self.smith.speak(f"Email {i}: From {email['sender']}, Subject: {email['subject']}")
                
            self.smith.speak("Would you like me to read any of these emails in full?")
            
        except Exception as e:
            self.logger.error(f"Email summarization failed: {e}")
            self.smith.speak("Error summarizing emails")

    def read_email(self, email_index):
        """Read full email content"""
        try:
            if not self.email_cache or not self.email_cache['emails']:
                self.smith.speak("No emails in cache. Let me check for new ones.")
                self.check_emails()
            
            if not self.email_cache['emails']:
                return
            
            emails = self.email_cache['emails']
            if email_index < 1 or email_index > len(emails):
                self.smith.speak("Invalid email number")
                return
            
            email = emails[email_index - 1]
            message = email['full_message']
            
            # Get email body
            body = ""
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = message.get_payload(decode=True).decode()
            
            self.smith.speak(f"Reading email from {email['sender']}")
            self.smith.speak(f"Subject: {email['subject']}")
            self.smith.speak("Message body:")
            self.smith.speak(body)
            
        except Exception as e:
            self.logger.error(f"Email reading failed: {e}")
            self.smith.speak("Error reading email")

class SocialMediaMonitor:
    """Social media monitoring and interaction"""
    def __init__(self, smith_instance):
        self.smith = smith_instance
        self.logger = smith_instance.logger
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Load Twitter/X API credentials
        self.load_credentials()

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
            self.smith.speak("Here are the current trending topics:")
            for i, trend in enumerate(trends, 1):
                self.smith.speak(f"{i}. {trend}")
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Failed to fetch trending topics: {e}")
            self.smith.speak("I couldn't fetch the trending topics. Would you like me to show you the news instead?")
            return None

    def get_news(self):
        """Fallback method to get news headlines"""
        try:
            import requests
            
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "country": "us",
                "apiKey": self.config.get("news_api_key")
            }
            
            response = requests.get(url, params=params)
            news = response.json()
            
            if news.get("status") == "ok":
                articles = news.get("articles", [])[:5]
                self.smith.speak("Here are the top news headlines:")
                for i, article in enumerate(articles, 1):
                    self.smith.speak(f"{i}. {article['title']}")
                
        except Exception as e:
            self.logger.error(f"Failed to fetch news: {e}")
            self.smith.speak("I'm having trouble accessing the news right now.")

if __name__ == "__main__":
    smith = SmithAssistant()
    smith.run()
