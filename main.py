import sys
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
import glob

class JarvisAssistant:
    """Main JARVIS Assistant class integrating all subsystems"""
    def __init__(self):
        # Initialize logger first for error tracking
        self.logger = JarvisLogger()
        
        # Initialize core systems
        self.version = "Mark 1.5"
        self.arc_reactor_status = "Online"
        
        # Initialize text-to-speech and speech recognition
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        
        # Initialize Ollama for AI processing
        try:
            self.ollama = ollama.Client()
            self.logger.info("Ollama AI system initialized")
        except Exception as e:
            self.logger.error(f"Ollama initialization failed: {e}")
            self.speak("AI processing systems offline")
        
        # Initialize audio control
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            self.is_muted = False
            self.previous_volume = 50  # Default volume level
        except Exception as e:
            self.logger.error(f"Audio control initialization failed: {e}")
        
        # Initialize pygame for sound effects
        try:
            pygame.mixer.init()
        except Exception as e:
            self.logger.error(f"Pygame initialization failed: {e}")
        
        # Initialize core subsystems
        self.power_management = self._init_power_management()
        self.security = self._init_security_system()
        self.workshop = self._init_workshop_interface()
        self.neural_interface = self._init_neural_interface()
        
        # Initialize suit interface
        self.suit_interface = SuitInterface()
        
        # Initialize memory system
        self.memory = JarvisMemory(self)
        
        # Initialize workshop mode
        self.workshop_mode = False
        
        # Start monitoring systems
        self._start_monitoring_systems()
        
        # Initialize scheduler for automated tasks
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Schedule regular maintenance tasks
        self._schedule_maintenance()

    def speak(self, text):
        """Speak text using text-to-speech"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Speech error: {e}")
            print(f"Speech output: {text}")

    def listen(self):
        """Listen for voice commands"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)
                command = self.recognizer.recognize_google(audio).lower()
                return command
        except sr.UnknownValueError:
            self.speak("I didn't catch that. Could you repeat?")
            return None
        except sr.RequestError:
            self.speak("Speech recognition service is offline")
            return None
        except Exception as e:
            self.logger.error(f"Listening error: {e}")
            return None

    def run(self):
        """Main assistant loop"""
        while True:
            try:
                command = self.listen()
                if command:
                    self.process_command(command)
            except KeyboardInterrupt:
                self.speak("Shutting down JARVIS systems")
                break
            except Exception as e:
                self.logger.error(f"Runtime error: {e}")
                self.speak("System error detected. Attempting recovery.")

    def process_command(self, command):
        """Process voice commands with AI understanding"""
        try:
            # Use Ollama for intent recognition
            response = self.ollama.chat(model='deepseek-r1', messages=[{
                'role': 'system',
                'content': 'You are JARVIS, processing user commands.'
            }, {
                'role': 'user',
                'content': command
            }])
            
            if response and 'message' in response:
                intent = self._extract_intent(response['message']['content'])
                self._execute_intent(intent, command)
            else:
                # Fallback to basic command processing
                self._process_basic_command(command)
                
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            # Fallback to basic intent extraction
            intent, category, params = self.fallback_intent_extraction(command)
            if intent and category:
                self._execute_intent({'intent': intent, 'category': category, 'params': params})
            else:
                self.speak("I'm having trouble processing that command")

    def _extract_intent(self, ai_response):
        """Extract intent from AI response"""
        try:
            # Basic intent extraction
            if "play" in ai_response.lower():
                return {"intent": "MEDIA", "category": "youtube", "params": {"query": ai_response}}
            elif "volume" in ai_response.lower():
                return {"intent": "MEDIA", "category": "volume_control"}
            elif "timer" in ai_response.lower():
                return {"intent": "PRODUCTIVITY", "category": "timer"}
            # Add more intent patterns as needed
            return {"intent": "UNKNOWN", "category": None}
        except Exception as e:
            self.logger.error(f"Intent extraction error: {e}")
            return {"intent": "ERROR", "category": None}

    def _execute_intent(self, intent, original_command=""):
        """Execute recognized intent"""
        try:
            if intent["intent"] == "MEDIA":
                if intent["category"] == "youtube":
                    self.play_youtube(intent["params"]["query"])
                elif intent["category"] == "volume_control":
                    self.set_volume(intent["params"].get("level", 50))
                    
            elif intent["intent"] == "PRODUCTIVITY":
                if intent["category"] == "timer":
                    duration = intent["params"].get("duration", 5)
                    self.timer(duration, intent["params"].get("label", ""))
                    
            elif intent["intent"] == "SYSTEM":
                if intent["category"] == "shutdown":
                    self.speak("Initiating shutdown sequence")
                    sys.exit(0)
                    
            else:
                self.speak("I'm not sure how to handle that command")
                
        except Exception as e:
            self.logger.error(f"Intent execution error: {e}")
            self.speak("Error executing command")

    def _process_basic_command(self, command):
        """Process basic commands without AI"""
        command = command.lower()
        
        if "youtube" in command or "play" in command:
            self.play_youtube(command)
        elif "volume" in command:
            try:
                level = int(''.join(filter(str.isdigit, command)))
                self.set_volume(level)
            except:
                self.speak("Could not understand volume level")
        elif "timer" in command:
            try:
                minutes = int(''.join(filter(str.isdigit, command)))
                self.timer(minutes)
            except:
                self.speak("Could not understand timer duration")
        else:
            self.speak("Command not recognized")

    def _schedule_maintenance(self):
        """Schedule regular maintenance tasks"""
        try:
            # Schedule memory backup every 6 hours
            self.scheduler.add_job(
                self.memory.save_memories,
                'interval',
                hours=6,
                id='memory_backup'
            )
            
            # Schedule system checks every hour
            self.scheduler.add_job(
                self._run_system_checks,
                'interval',
                hours=1,
                id='system_checks'
            )
            
        except Exception as e:
            self.logger.error(f"Maintenance scheduling error: {e}")

    def _run_system_checks(self):
        """Run periodic system checks"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > 90:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"High memory usage: {memory.percent}%")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"Low disk space: {disk.percent}% used")
            
        except Exception as e:
            self.logger.error(f"System check error: {e}")

    def toggle_workshop_mode(self):
        """Toggle workshop mode"""
        try:
            self.workshop_mode = not self.workshop_mode
            if self.workshop_mode:
                if self.workshop_mode_features():
                    self.speak("Workshop mode activated. All systems online.")
                else:
                    self.workshop_mode = False
                    self.speak("Workshop mode activation failed.")
            else:
                self.speak("Workshop mode deactivated.")
        except Exception as e:
            self.logger.error(f"Workshop mode toggle error: {e}")
            self.speak("Error toggling workshop mode")

    def _init_power_management(self):
        """Initialize power management for arc reactor simulation"""
        return {
            "current_output": 100,  # Current power output percentage
            "efficiency": 97.3,     # Arc reactor efficiency
            "temperature": 62.4,    # Core temperature in Celsius
            "estimated_life": "8760h",  # Estimated reactor life in hours
            "power_distribution": {
                "main_systems": 45,
                "life_support": 15,
                "neural_interface": 10,
                "security": 20,
                "reserve": 10
            },
            "backup_power": {
                "status": "STANDBY",
                "capacity": 100,
                "type": "Secondary Arc Reactor"
            }
        }
    
    def _init_security_system(self):
        """Initialize security protocols"""
        return {
            "perimeter_sensors": True,
            "motion_detection": True,
            "facial_recognition": True,
            "threat_analysis": True,
            "quantum_encryption": {
                "status": "ACTIVE",
                "key_rotation": "AUTO",
                "encryption_level": "QUANTUM_256"
            },
            "defense_systems": {
                "automated_turrets": "STANDBY",
                "energy_shields": "STANDBY",
                "emergency_lockdown": "READY"
            }
        }
        
    def _init_workshop_interface(self):
        """Initialize workshop management system"""
        return {
            "3d_printer_status": "Ready",
            "fabrication_units": "Online",
            "robotic_assistants": {
                "DUM-E": {"status": "Online", "task": "Fire Safety"},
                "U": {"status": "Online", "task": "Tool Management"},
                "BUTTERFINGERS": {"status": "Online", "task": "Assembly"}
            },
            "inventory_system": {
                "status": "Active",
                "low_stock_alerts": True,
                "auto_reorder": True
            },
            "environmental_controls": {
                "temperature": 20.5,
                "humidity": 45,
                "air_filtration": "Active",
                "ventilation": "Auto"
            }
        }

    def _init_neural_interface(self):
        """Initialize neural interface for suit control"""
        return {
            "status": "STANDBY",
            "connection_type": "QUANTUM_NEURAL",
            "response_time": "0.001ms",
            "thought_prediction": True,
            "neural_calibration": 100,
            "emergency_override": "READY"
        }

    def set_volume(self, level):
        """Set system volume level"""
        try:
            level = max(0, min(100, level))  # Ensure level is between 0 and 100
            self.volume.SetMasterVolumeLevelScalar(level / 100, None)
            self.previous_volume = level
            self.speak(f"Volume set to {level} percent")
        except Exception as e:
            self.logger.error(f"Volume control error: {e}")
            self.speak("Volume control malfunction")

    def _start_monitoring_systems(self):
        """Start all monitoring systems in separate threads"""
        try:
            monitoring_threads = [
                threading.Thread(target=self._monitor_arc_reactor, daemon=True),
                threading.Thread(target=self._monitor_security, daemon=True),
                threading.Thread(target=self._monitor_workshop, daemon=True),
                threading.Thread(target=self._monitor_neural_interface, daemon=True)
            ]
            for thread in monitoring_threads:
                thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start monitoring systems: {e}")

    def _monitor_arc_reactor(self):
        """Monitor arc reactor status and performance"""
        while True:
            try:
                # Simulate real-time monitoring
                current_temp = self.power_management["temperature"]
                current_output = self.power_management["current_output"]
                
                # Check for critical conditions
                if current_temp > 80:
                    self._trigger_emergency_protocol("arc_reactor_overheat")
                if current_output < 50:
                    self._trigger_emergency_protocol("arc_reactor_low_power")
                
                # Update efficiency based on temperature
                self.power_management["efficiency"] = 100 - (current_temp - 60) * 0.5
                
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Arc reactor monitoring error: {e}")
                time.sleep(5)  # Wait before retrying

    def _monitor_security(self):
        """Monitor security systems and threats"""
        while True:
            try:
                # Simulate security monitoring
                if self.security["threat_analysis"]:
                    threat_level = self._analyze_threats()
                    if threat_level > 7:
                        self._trigger_emergency_protocol("security_breach")
                
                # Rotate encryption keys
                if self.security["quantum_encryption"]["key_rotation"] == "AUTO":
                    self._rotate_encryption_keys()
                
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                self.logger.error(f"Security monitoring error: {e}")
                time.sleep(5)

    def _monitor_workshop(self):
        """Monitor workshop conditions and equipment"""
        while True:
            try:
                # Monitor environmental conditions
                env = self.workshop["environmental_controls"]
                if env["temperature"] > 30 or env["humidity"] > 70:
                    self._adjust_environmental_controls()
                
                # Check robotic assistants
                for assistant, data in self.workshop["robotic_assistants"].items():
                    if data["status"] == "Error":
                        self.logger.warning(f"{assistant} needs attention")
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                self.logger.error(f"Workshop monitoring error: {e}")
                time.sleep(10)

    def _monitor_neural_interface(self):
        """Monitor neural interface performance"""
        while True:
            try:
                if self.neural_interface["status"] == "ACTIVE":
                    # Monitor neural response time
                    if float(self.neural_interface["response_time"].replace("ms", "")) > 0.1:
                        self._recalibrate_neural_interface()
                    
                    # Update thought prediction model
                    if self.neural_interface["thought_prediction"]:
                        self._update_thought_prediction()
                
                time.sleep(0.1)  # Check every 100ms for real-time response
            except Exception as e:
                self.logger.error(f"Neural interface monitoring error: {e}")
                time.sleep(1)

    def _trigger_emergency_protocol(self, protocol_name):
        """Handle emergency protocols"""
        try:
            if protocol_name == "arc_reactor_overheat":
                self.power_management["power_distribution"]["main_systems"] -= 20
                self.power_management["power_distribution"]["cooling"] = 20
            elif protocol_name == "security_breach":
                self.security["defense_systems"]["energy_shields"] = "ACTIVE"
                self.workshop["workshop_lockdown"] = True
            elif protocol_name == "neural_interface_failure":
                self.neural_interface["status"] = "EMERGENCY_SHUTDOWN"
                self.neural_interface["emergency_override"] = "ACTIVE"
            
            self.logger.warning(f"Emergency protocol triggered: {protocol_name}")
            self.speak(f"Emergency protocol {protocol_name} activated")
        except Exception as e:
            self.logger.error(f"Failed to trigger emergency protocol: {e}")

    def _analyze_threats(self):
        """Analyze potential security threats"""
        # Placeholder for threat analysis logic
        return random.randint(0, 10)  # Simulate threat level

    def _rotate_encryption_keys(self):
        """Rotate quantum encryption keys"""
        try:
            # Simulate quantum key rotation
            self.security["quantum_encryption"]["last_rotation"] = datetime.datetime.now()
        except Exception as e:
            self.logger.error(f"Failed to rotate encryption keys: {e}")

    def _adjust_environmental_controls(self):
        """Adjust workshop environmental controls"""
        try:
            current_temp = self.workshop["environmental_controls"]["temperature"]
            if current_temp > 25:
                self.workshop["environmental_controls"]["ventilation"] = "Maximum"
            else:
                self.workshop["environmental_controls"]["ventilation"] = "Auto"
        except Exception as e:
            self.logger.error(f"Failed to adjust environmental controls: {e}")

    def _recalibrate_neural_interface(self):
        """Recalibrate neural interface"""
        try:
            self.neural_interface["neural_calibration"] = 100
            self.neural_interface["response_time"] = "0.001ms"
        except Exception as e:
            self.logger.error(f"Failed to recalibrate neural interface: {e}")

    def _update_thought_prediction(self):
        """Update thought prediction model"""
        try:
            # Placeholder for thought prediction model update
            pass
        except Exception as e:
            self.logger.error(f"Failed to update thought prediction model: {e}")

class JarvisCore:
    """Core JARVIS system with enhanced capabilities"""
    def __init__(self):
        self.version = "Mark 1.5"
        self.arc_reactor_status = "Online"
        self.security_protocols = {
            "intruder_detection": True,
            "workshop_lockdown": False,
            "suit_protocols": ["House Party Protocol", "Clean Slate Protocol"],
            "biometric_auth": True,
            "quantum_encryption": True,
            "emergency_protocols": {
                "arc_reactor_failure": "ACTIVE",
                "suit_breach": "STANDBY",
                "workshop_breach": "STANDBY"
            }
        }
        
        # Initialize advanced subsystems
        self.power_management = self._init_power_management()
        self.security = self._init_security_system()
        self.workshop = self._init_workshop_interface()
        self.neural_interface = self._init_neural_interface()
        
        # Start monitoring threads
        self._start_monitoring_systems()
        
    def _init_power_management(self):
        """Initialize advanced power management for arc reactor simulation"""
        return {
            "current_output": 100,  # Current power output percentage
            "efficiency": 97.3,     # Arc reactor efficiency
            "temperature": 62.4,    # Core temperature in Celsius
            "estimated_life": "8760h",  # Estimated reactor life in hours
            "power_distribution": {
                "main_systems": 45,
                "life_support": 15,
                "neural_interface": 10,
                "security": 20,
                "reserve": 10
            },
            "backup_power": {
                "status": "STANDBY",
                "capacity": 100,
                "type": "Secondary Arc Reactor"
            }
        }
    
    def _init_security_system(self):
        """Initialize advanced security protocols"""
        return {
            "perimeter_sensors": True,
            "motion_detection": True,
            "facial_recognition": True,
            "threat_analysis": True,
            "quantum_encryption": {
                "status": "ACTIVE",
                "key_rotation": "AUTO",
                "encryption_level": "QUANTUM_256"
            },
            "defense_systems": {
                "automated_turrets": "STANDBY",
                "energy_shields": "STANDBY",
                "emergency_lockdown": "READY"
            }
        }
        
    def _init_workshop_interface(self):
        """Initialize advanced workshop management system"""
        return {
            "3d_printer_status": "Ready",
            "fabrication_units": "Online",
            "robotic_assistants": {
                "DUM-E": {"status": "Online", "task": "Fire Safety"},
                "U": {"status": "Online", "task": "Tool Management"},
                "BUTTERFINGERS": {"status": "Online", "task": "Assembly"}
            },
            "inventory_system": {
                "status": "Active",
                "low_stock_alerts": True,
                "auto_reorder": True
            },
            "environmental_controls": {
                "temperature": 20.5,
                "humidity": 45,
                "air_filtration": "Active",
                "ventilation": "Auto"
            }
        }

    def _init_neural_interface(self):
        """Initialize neural interface for suit control"""
        return {
            "status": "STANDBY",
            "connection_type": "QUANTUM_NEURAL",
            "response_time": "0.001ms",
            "thought_prediction": True,
            "neural_calibration": 100,
            "emergency_override": "READY"
        }

    def _start_monitoring_systems(self):
        """Start all monitoring systems in separate threads"""
        try:
            monitoring_threads = [
                threading.Thread(target=self._monitor_arc_reactor, daemon=True),
                threading.Thread(target=self._monitor_security, daemon=True),
                threading.Thread(target=self._monitor_workshop, daemon=True),
                threading.Thread(target=self._monitor_neural_interface, daemon=True)
            ]
            for thread in monitoring_threads:
                thread.start()
        except Exception as e:
            logging.error(f"Failed to start monitoring systems: {e}")

    def _monitor_arc_reactor(self):
        """Monitor arc reactor status and performance"""
        while True:
            try:
                # Simulate real-time monitoring
                current_temp = self.power_management["temperature"]
                current_output = self.power_management["current_output"]
                
                # Check for critical conditions
                if current_temp > 80:
                    self._trigger_emergency_protocol("arc_reactor_overheat")
                if current_output < 50:
                    self._trigger_emergency_protocol("arc_reactor_low_power")
                
                # Update efficiency based on temperature
                self.power_management["efficiency"] = 100 - (current_temp - 60) * 0.5
                
                time.sleep(1)  # Check every second
            except Exception as e:
                logging.error(f"Arc reactor monitoring error: {e}")
                time.sleep(5)  # Wait before retrying

    def _monitor_security(self):
        """Monitor security systems and threats"""
        while True:
            try:
                # Simulate security monitoring
                if self.security["threat_analysis"]:
                    threat_level = self._analyze_threats()
                    if threat_level > 7:
                        self._trigger_emergency_protocol("security_breach")
                
                # Rotate encryption keys
                if self.security["quantum_encryption"]["key_rotation"] == "AUTO":
                    self._rotate_encryption_keys()
                
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logging.error(f"Security monitoring error: {e}")
                time.sleep(5)

    def _monitor_workshop(self):
        """Monitor workshop conditions and equipment"""
        while True:
            try:
                # Monitor environmental conditions
                env = self.workshop["environmental_controls"]
                if env["temperature"] > 30 or env["humidity"] > 70:
                    self._adjust_environmental_controls()
                
                # Check robotic assistants
                for assistant, data in self.workshop["robotic_assistants"].items():
                    if data["status"] == "Error":
                        logging.warning(f"{assistant} needs attention")
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logging.error(f"Workshop monitoring error: {e}")
                time.sleep(10)

    def _monitor_neural_interface(self):
        """Monitor neural interface performance"""
        while True:
            try:
                if self.neural_interface["status"] == "ACTIVE":
                    # Monitor neural response time
                    if float(self.neural_interface["response_time"].replace("ms", "")) > 0.1:
                        self._recalibrate_neural_interface()
                    
                    # Update thought prediction model
                    if self.neural_interface["thought_prediction"]:
                        self._update_thought_prediction()
                
                time.sleep(0.1)  # Check every 100ms for real-time response
            except Exception as e:
                logging.error(f"Neural interface monitoring error: {e}")
                time.sleep(1)

    def _trigger_emergency_protocol(self, protocol_name):
        """Handle emergency protocols"""
        try:
            if protocol_name == "arc_reactor_overheat":
                self.power_management["power_distribution"]["main_systems"] -= 20
                self.power_management["power_distribution"]["cooling"] = 20
            elif protocol_name == "security_breach":
                self.security["defense_systems"]["energy_shields"] = "ACTIVE"
                self.workshop["workshop_lockdown"] = True
            elif protocol_name == "neural_interface_failure":
                self.neural_interface["status"] = "EMERGENCY_SHUTDOWN"
                self.neural_interface["emergency_override"] = "ACTIVE"
            
            logging.warning(f"Emergency protocol triggered: {protocol_name}")
        except Exception as e:
            logging.error(f"Failed to trigger emergency protocol: {e}")

    def _analyze_threats(self):
        """Analyze potential security threats"""
        # Placeholder for threat analysis logic
        return random.randint(0, 10)  # Simulate threat level

    def _rotate_encryption_keys(self):
        """Rotate quantum encryption keys"""
        try:
            # Simulate quantum key rotation
            self.security["quantum_encryption"]["last_rotation"] = datetime.datetime.now()
        except Exception as e:
            logging.error(f"Failed to rotate encryption keys: {e}")

    def _adjust_environmental_controls(self):
        """Adjust workshop environmental controls"""
        try:
            current_temp = self.workshop["environmental_controls"]["temperature"]
            if current_temp > 25:
                self.workshop["environmental_controls"]["ventilation"] = "Maximum"
            else:
                self.workshop["environmental_controls"]["ventilation"] = "Auto"
        except Exception as e:
            logging.error(f"Failed to adjust environmental controls: {e}")

    def _recalibrate_neural_interface(self):
        """Recalibrate neural interface"""
        try:
            self.neural_interface["neural_calibration"] = 100
            self.neural_interface["response_time"] = "0.001ms"
        except Exception as e:
            logging.error(f"Failed to recalibrate neural interface: {e}")

    def _update_thought_prediction(self):
        """Update thought prediction model"""
        try:
            # Placeholder for thought prediction model update
            pass
        except Exception as e:
            logging.error(f"Failed to update thought prediction model: {e}")

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

class JarvisMemory:
    """Advanced memory and learning system for JARVIS"""
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.logger = jarvis_instance.logger
        self.memory_file = 'jarvis_memory.json'
        self.short_term = []  # Recent interactions
        self.long_term = {}   # Permanent storage
        self.max_short_term = 50  # Maximum number of recent memories
        
        # Enhanced memory categories
        self.categories = {
            "conversations": [],
            "commands": {},
            "preferences": {},
            "project_data": {},
            "learned_responses": {},
            "important_dates": {},
            "workshop_notes": [],
            "suit_data": {},
            "security_events": [],
            "system_improvements": [],
            "user_patterns": {},
            "error_history": {},
            "maintenance_logs": []
        }
        
        # Initialize learning system
        self.learning_system = {
            "pattern_recognition": {
                "command_patterns": {},
                "conversation_patterns": {},
                "behavior_patterns": {}
            },
            "response_optimization": {
                "successful_responses": {},
                "failed_responses": {},
                "improvement_suggestions": []
            },
            "knowledge_base": {
                "technical": {},
                "conversational": {},
                "procedures": {},
                "preferences": {}
            }
        }
        
        # Load existing memories
        self.load_memories()
        
        # Start memory management
        threading.Thread(target=self._memory_maintenance_loop, daemon=True).start()

    def load_memories(self):
        """Load and validate memories from storage"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    if self._validate_memory_data(data):
                        self.long_term = data.get('long_term', {})
                        self.categories = data.get('categories', self.categories)
                        self.learning_system["knowledge_base"] = data.get('knowledge_base', 
                            self.learning_system["knowledge_base"])
                        self.jarvis.speak("Memory systems online and validated")
                    else:
                        raise ValueError("Memory data validation failed")
            else:
                self.jarvis.speak("Creating new memory banks")
                self.save_memories()
        except Exception as e:
            self.logger.error(f"Memory load error: {e}")
            self.jarvis.speak("Memory retrieval systems offline")

    def _validate_memory_data(self, data):
        """Validate loaded memory data"""
        try:
            required_keys = ['long_term', 'categories', 'knowledge_base']
            if not all(key in data for key in required_keys):
                return False
                
            # Validate memory structure
            if not isinstance(data['long_term'], dict):
                return False
            if not isinstance(data['categories'], dict):
                return False
                
            # Validate knowledge base
            kb = data.get('knowledge_base', {})
            if not all(isinstance(kb.get(k, {}), dict) for k in 
                ['technical', 'conversational', 'procedures', 'preferences']):
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Memory validation error: {e}")
            return False

    def save_memories(self):
        """Save memories with backup"""
        try:
            # Create backup before saving
            if os.path.exists(self.memory_file):
                backup_file = f"{self.memory_file}.backup"
                shutil.copy2(self.memory_file, backup_file)
            
            memory_data = {
                'long_term': self.long_term,
                'categories': self.categories,
                'knowledge_base': self.learning_system["knowledge_base"],
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(memory_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Memory save error: {e}")

    def remember(self, category, data, important=False):
        """Enhanced memory storage with pattern learning"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            memory = {
                'timestamp': timestamp,
                'data': data,
                'important': important,
                'context': self._get_current_context()
            }
            
            # Add to short-term memory
            self.short_term.append(memory)
            if len(self.short_term) > self.max_short_term:
                oldest = self.short_term.pop(0)
                if oldest['important']:
                    self.long_term[oldest['timestamp']] = oldest
            
            # Store in appropriate category
            if category in self.categories:
                if isinstance(self.categories[category], list):
                    self.categories[category].append(memory)
                elif isinstance(self.categories[category], dict):
                    key = data.get('key', timestamp)
                    self.categories[category][key] = memory
            
            # Important memories go to long-term storage
            if important:
                self.long_term[timestamp] = memory
                
            # Learn from new memory
            self._learn_from_memory(category, memory)
            
            # Save after important memories
            if important:
                self.save_memories()
                
            return True
        except Exception as e:
            self.logger.error(f"Memory storage error: {e}")
            return False

    def _get_current_context(self):
        """Get current system context"""
        return {
            "workshop_mode": self.jarvis.workshop_mode if hasattr(self.jarvis, 'workshop_mode') else False,
            "current_suit": self.jarvis.suit_interface.current_suit if hasattr(self.jarvis, 'suit_interface') else None,
            "system_status": self.jarvis.arc_reactor_status if hasattr(self.jarvis, 'arc_reactor_status') else "Unknown"
        }

    def _learn_from_memory(self, category, memory):
        """Learn patterns and improve from new memories"""
        try:
            # Update pattern recognition
            if category == "commands":
                self._update_command_patterns(memory)
            elif category == "conversations":
                self._update_conversation_patterns(memory)
            
            # Update knowledge base
            self._update_knowledge_base(category, memory)
            
            # Analyze for improvements
            if category in ["error_history", "system_improvements"]:
                self._analyze_for_improvements(memory)
        except Exception as e:
            self.logger.error(f"Learning error: {e}")

    def _update_command_patterns(self, memory):
        """Update command pattern recognition"""
        try:
            command_data = memory['data']
            if 'command' in command_data and 'success' in command_data:
                pattern = command_data['command'].lower()
                success = command_data['success']
                
                patterns = self.learning_system["pattern_recognition"]["command_patterns"]
                if pattern not in patterns:
                    patterns[pattern] = {"success": 0, "failure": 0}
                
                if success:
                    patterns[pattern]["success"] += 1
                else:
                    patterns[pattern]["failure"] += 1
        except Exception as e:
            self.logger.error(f"Command pattern update error: {e}")

    def _update_conversation_patterns(self, memory):
        """Update conversation pattern recognition"""
        try:
            conv_data = memory['data']
            patterns = self.learning_system["pattern_recognition"]["conversation_patterns"]
            
            if 'user' in conv_data:
                phrases = self._extract_key_phrases(conv_data['user'])
                for phrase in phrases:
                    if phrase not in patterns:
                        patterns[phrase] = {"count": 0, "responses": {}}
                    patterns[phrase]["count"] += 1
                    
                    if 'jarvis' in conv_data:
                        response = conv_data['jarvis']
                        if response not in patterns[phrase]["responses"]:
                            patterns[phrase]["responses"][response] = 0
                        patterns[phrase]["responses"][response] += 1
        except Exception as e:
            self.logger.error(f"Conversation pattern update error: {e}")

    def _extract_key_phrases(self, text):
        """Extract key phrases from text"""
        words = text.lower().split()
        phrases = []
        for i in range(len(words)):
            if i < len(words) - 1:
                phrases.append(f"{words[i]} {words[i+1]}")
        return phrases

    def _update_knowledge_base(self, category, memory):
        """Update knowledge base with new information"""
        try:
            kb = self.learning_system["knowledge_base"]
            
            if category == "technical":
                if 'topic' in memory['data']:
                    topic = memory['data']['topic']
                    if topic not in kb["technical"]:
                        kb["technical"][topic] = []
                    kb["technical"][topic].append(memory['data'])
            
            elif category == "conversational":
                if 'pattern' in memory['data']:
                    pattern = memory['data']['pattern']
                    if pattern not in kb["conversational"]:
                        kb["conversational"][pattern] = []
                    kb["conversational"][pattern].append(memory['data'])
        except Exception as e:
            self.logger.error(f"Knowledge base update error: {e}")

    def _analyze_for_improvements(self, memory):
        """Analyze memory for potential system improvements"""
        try:
            if 'error' in memory['data']:
                error = memory['data']['error']
                if error not in self.categories['error_history']:
                    self.categories['error_history'][error] = []
                self.categories['error_history'][error].append(memory)
                
                if len(self.categories['error_history'][error]) >= 3:
                    self._suggest_improvement(error)
        except Exception as e:
            self.logger.error(f"Improvement analysis error: {e}")

    def _suggest_improvement(self, error_pattern):
        """Generate improvement suggestions"""
        try:
            improvements = self.learning_system["response_optimization"]["improvement_suggestions"]
            
            suggestion = {
                "error_pattern": error_pattern,
                "frequency": len(self.categories['error_history'][error_pattern]),
                "timestamp": datetime.datetime.now().isoformat(),
                "suggestion": f"Consider implementing error handling for: {error_pattern}"
            }
            
            improvements.append(suggestion)
            
            if hasattr(self.jarvis, 'ollama'):
                self._generate_improvement_with_ollama(error_pattern)
        except Exception as e:
            self.logger.error(f"Improvement suggestion error: {e}")

    def _generate_improvement_with_ollama(self, error_pattern):
        """Generate improvement suggestion using Ollama"""
        try:
            prompt = f"""As JARVIS, analyze this error pattern and suggest improvements:
            Error Pattern: {error_pattern}
            Context: Python AI Assistant
            Goal: Improve error handling and system reliability"""
            
            response = self.jarvis.ollama.chat(model='deepseek-r1', messages=[{
                'role': 'system',
                'content': 'You are JARVIS, analyzing system improvements.'
            }, {
                'role': 'user',
                'content': prompt
            }])
            
            if response and 'message' in response:
                suggestion = response['message']['content']
                self.learning_system["response_optimization"]["improvement_suggestions"].append({
                    "error_pattern": error_pattern,
                    "ai_suggestion": suggestion,
                    "timestamp": datetime.datetime.now().isoformat()
                })
        except Exception as e:
            self.logger.error(f"Ollama improvement generation error: {e}")

    def _memory_maintenance_loop(self):
        """Periodic memory maintenance tasks"""
        while True:
            try:
                # Consolidate short-term memories
                current_time = datetime.datetime.now()
                for memory in self.short_term[:]:
                    memory_time = datetime.datetime.strptime(memory['timestamp'], 
                        "%Y-%m-%d %H:%M:%S")
                    if (current_time - memory_time).total_seconds() > 3600 and memory['important']:
                        self.long_term[memory['timestamp']] = memory
                        self.short_term.remove(memory)
                
                # Clean up old memories
                old_threshold = current_time - datetime.timedelta(days=30)
                for timestamp, memory in list(self.long_term.items()):
                    memory_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    if memory_time < old_threshold and not memory['important']:
                        del self.long_term[timestamp]
                
                # Optimize storage
                for category in self.categories:
                    if isinstance(self.categories[category], list):
                        self.categories[category] = self.categories[category][-1000:]
                
                time.sleep(3600)  # Run maintenance every hour
            except Exception as e:
                self.logger.error(f"Memory maintenance error: {e}")
                time.sleep(300)  # Retry after 5 minutes

    def recall(self, category=None, query=None, limit=5):
        """Enhanced memory recall with pattern matching"""
        try:
            results = []
            
            # Search in specific category
            if category and category in self.categories:
                memories = self.categories[category]
                if query:
                    if isinstance(memories, list):
                        results.extend([m for m in memories 
                            if self._memory_matches_query(m, query)])
                    elif isinstance(memories, dict):
                        results.extend([v for v in memories.values() 
                            if self._memory_matches_query(v, query)])
                else:
                    if isinstance(memories, list):
                        results.extend(memories)
                    elif isinstance(memories, dict):
                        results.extend(memories.values())
            
            # Search all categories if none specified
            elif query:
                for cat, memories in self.categories.items():
                    if isinstance(memories, list):
                        results.extend([m for m in memories 
                            if self._memory_matches_query(m, query)])
                    elif isinstance(memories, dict):
                        results.extend([v for v in memories.values() 
                            if self._memory_matches_query(v, query)])
            
            # Sort by timestamp and importance
            results.sort(key=lambda x: (x['important'], x['timestamp']), reverse=True)
            
            return results[:limit]
        except Exception as e:
            self.logger.error(f"Memory recall error: {e}")
            return []

    def _memory_matches_query(self, memory, query):
        """Check if memory matches search query"""
        try:
            query = query.lower()
            memory_str = str(memory['data']).lower()
            
            # Direct match
            if query in memory_str:
                return True
            
            # Pattern match
            patterns = self.learning_system["pattern_recognition"]["command_patterns"]
            if query in patterns:
                return True
            
            # Semantic match using Ollama if available
            if hasattr(self.jarvis, 'ollama'):
                similarity = self._calculate_semantic_similarity(query, memory_str)
                return similarity > 0.8
            
            return False
        except Exception as e:
            self.logger.error(f"Memory matching error: {e}")
            return False

    def _calculate_semantic_similarity(self, query, text):
        """Calculate semantic similarity using Ollama"""
        try:
            response = self.jarvis.ollama.chat(model='deepseek-r1', messages=[{
                'role': 'system',
                'content': 'Calculate semantic similarity between two texts (0-1).'
            }, {
                'role': 'user',
                'content': f"Text 1: {query}\nText 2: {text}"
            }])
            
            if response and 'message' in response:
                # Extract similarity score from response
                try:
                    score = float(response['message']['content'])
                    return min(max(score, 0), 1)  # Ensure score is between 0 and 1
                except:
                    return 0.5
            return 0.5
        except Exception as e:
            self.logger.error(f"Semantic similarity calculation error: {e}")
            return 0.5

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
        
        # System patterns
        if "shutdown" in command or "exit" in command:
            return "SYSTEM", "shutdown", {}
        
        return None, None, {}

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
            try:
                pygame.mixer.music.load('alert.wav')
                pygame.mixer.music.play()
            except Exception as e:
                self.logger.error(f"Alert sound failed: {e}")

        try:
            minutes = int(duration)
            threading.Timer(minutes * 60, timer_done).start()
            self.speak(f"Timer set for {minutes} minutes. {label}")
        except Exception as e:
            self.logger.error(f"Timer error: {e}")
            self.speak("Failed to set timer. Please try again.")

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
            
            # Open YouTube search results
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
            self.logger.error(f"YouTube playback failed: {e}")
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

    def workshop_mode_features(self):
        """Enhanced workshop mode with project tracking"""
        try:
            # Add project tracking
            self.current_project = None
            self.project_timers = {}
            self.measurements = []
            self.safety_checks = {
                "ventilation": False,
                "power_stable": False,
                "safety_gear": False
            }
            
            # Add workshop commands
            self.workshop_commands = {
                "start project": self.start_project,
                "end project": self.end_project,
                "save measurement": self.save_measurement,
                "safety check": self.run_safety_check,
                "tool tracking": self.track_tools,
                "quick calc": self.quick_calculation
            }
            
            return True
        except Exception as e:
            self.logger.error(f"Workshop mode initialization failed: {e}")
            return False

    def start_project(self, project_name=None):
        """Start a new project with timing and tracking"""
        try:
            if not project_name:
                self.speak("What should I call this project, boss?")
                project_name = self.listen()
            
            self.current_project = project_name
            self.project_timers[project_name] = {
                "start_time": datetime.datetime.now(),
                "breaks": [],
                "total_time": 0
            }
            
            # Store in memory
            if hasattr(self, 'memory') and self.memory:
                self.memory.remember('project_data', {
                    'project': project_name,
                    'action': 'start',
                    'timestamp': datetime.datetime.now().isoformat()
                }, important=True)
            
            self.speak(f"Project {project_name} started. Timer running.")
            
        except Exception as e:
            self.logger.error(f"Error starting project: {e}")
            self.speak("Failed to start project tracking")

    def end_project(self, project_name=None):
        """End project and save data"""
        try:
            if not project_name:
                project_name = self.current_project
            
            if project_name in self.project_timers:
                end_time = datetime.datetime.now()
                start_time = self.project_timers[project_name]["start_time"]
                total_time = (end_time - start_time).total_seconds() / 3600  # Hours
                
                # Store project completion
                if hasattr(self, 'memory') and self.memory:
                    self.memory.remember('project_data', {
                        'project': project_name,
                        'action': 'complete',
                        'total_time': total_time,
                        'timestamp': end_time.isoformat()
                    }, important=True)
                
                self.speak(f"Project {project_name} completed. Total time: {total_time:.1f} hours")
                del self.project_timers[project_name]
                self.current_project = None
            else:
                self.speak("No active project found with that name")
                
        except Exception as e:
            self.logger.error(f"Error ending project: {e}")
            self.speak("Failed to end project tracking")

    def save_measurement(self, measurement):
        """Save workshop measurements"""
        try:
            if isinstance(measurement, str):
                # Try to parse measurement string
                try:
                    value = float(''.join(filter(str.isdigit, measurement)))
                    unit = ''.join(filter(str.isalpha, measurement))
                    measurement = {"value": value, "unit": unit}
                except:
                    self.speak("Could not parse measurement format")
                    return
            
            self.measurements.append({
                "measurement": measurement,
                "timestamp": datetime.datetime.now().isoformat(),
                "project": self.current_project
            })
            
            self.speak(f"Measurement saved: {measurement['value']} {measurement['unit']}")
            
        except Exception as e:
            self.logger.error(f"Error saving measurement: {e}")
            self.speak("Failed to save measurement")

    def run_safety_check(self):
        """Run workshop safety checks"""
        try:
            checks = {
                "ventilation": self._check_ventilation(),
                "power": self._check_power_stability(),
                "safety_gear": self._check_safety_gear(),
                "emergency_systems": self._check_emergency_systems(),
                "tool_status": self._check_tool_status()
            }
            
            all_passed = all(checks.values())
            if all_passed:
                self.speak("All safety checks passed. Workshop is secure.")
            else:
                failed = [k for k, v in checks.items() if not v]
                self.speak(f"Safety check failed for: {', '.join(failed)}")
            
            return all_passed
            
        except Exception as e:
            self.logger.error(f"Safety check error: {e}")
            self.speak("Error running safety checks")
            return False

    def _check_ventilation(self):
        """Check workshop ventilation"""
        try:
            return self.workshop["environmental_controls"]["ventilation"] == "Active"
        except:
            return False

    def _check_power_stability(self):
        """Check power systems stability"""
        try:
            return (self.power_management["efficiency"] > 90 and 
                    self.power_management["current_output"] > 80)
        except:
            return False

    def _check_safety_gear(self):
        """Check if safety gear is in place"""
        # Placeholder - would integrate with actual sensors
        return True

    def _check_emergency_systems(self):
        """Check emergency systems status"""
        try:
            return (self.security["defense_systems"]["emergency_lockdown"] == "READY" and
                    self.power_management["backup_power"]["status"] == "STANDBY")
        except:
            return False

    def _check_tool_status(self):
        """Check status of workshop tools"""
        try:
            return all(assistant["status"] == "Online" 
                      for assistant in self.workshop["robotic_assistants"].values())
        except:
            return False

    def track_tools(self):
        """Track workshop tools and equipment"""
        try:
            tools = {
                "3D Printer": self.workshop["3d_printer_status"],
                "Fabrication Units": self.workshop["fabrication_units"],
                "DUM-E": self.workshop["robotic_assistants"]["DUM-E"]["status"],
                "U": self.workshop["robotic_assistants"]["U"]["status"],
                "BUTTERFINGERS": self.workshop["robotic_assistants"]["BUTTERFINGERS"]["status"]
            }
            
            status_report = []
            for tool, status in tools.items():
                status_report.append(f"{tool}: {status}")
            
            self.speak("Workshop tool status:")
            for report in status_report:
                self.speak(report)
                
        except Exception as e:
            self.logger.error(f"Tool tracking error: {e}")
            self.speak("Error accessing tool tracking systems")

    def quick_calculation(self, formula=None):
        """Quick engineering calculations"""
        try:
            if not formula:
                self.speak("What's the calculation, boss?")
                formula = self.listen()
            
            # Clean up the formula
            formula = formula.lower().replace('x', '*')
            formula = formula.replace('divided by', '/')
            formula = formula.replace('times', '*')
            formula = formula.replace('plus', '+')
            formula = formula.replace('minus', '-')
            
            # Evaluate the formula
            result = eval(formula)
            self.speak(f"The result is {result}")
            
            # Store calculation in memory
            if hasattr(self, 'memory') and self.memory:
                self.memory.remember('calculations', {
                    'formula': formula,
                    'result': result,
                    'project': self.current_project
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Calculation error: {e}")
            self.speak("Error performing calculation. Please try again.")
            return None

class SuitInterface:
    """Advanced interface for Iron Man suits"""
    def __init__(self):
        self.active_suits = {}
        self.deployment_systems = {
            "Hall of Armor": {"status": "READY", "capacity": 10},
            "Suitcase": {"status": "READY", "type": "Mark V"},
            "Orbital": {"status": "STANDBY", "satellites": 4}
        }
        self.current_suit = None
        self.suit_systems = self._init_suit_systems()
        
        # Start suit monitoring
        self._start_suit_monitoring()
        
    def _init_suit_systems(self):
        """Initialize suit systems"""
        return {
            "power": {
                "arc_reactor": {"output": 100, "efficiency": 98.5},
                "backup_power": {"status": "STANDBY", "charge": 100}
            },
            "life_support": {
                "oxygen_levels": 100,
                "pressure": "NORMAL",
                "temperature": 20.5
            },
            "weapons": {
                "repulsors": {"status": "READY", "power": 100},
                "unibeam": {"status": "CHARGED", "power": 100},
                "missiles": {"count": 12, "status": "ARMED"}
            },
            "flight_systems": {
                "thrusters": {"status": "READY", "power": 100},
                "stabilizers": {"status": "ACTIVE"},
                "navigation": {"mode": "AI_ASSISTED"}
            },
            "defense": {
                "shields": {"status": "READY", "power": 100},
                "armor_integrity": 100,
                "countermeasures": {"flares": 24, "chaff": 12}
            },
            "ai_systems": {
                "targeting": {"status": "ACTIVE", "accuracy": 98.5},
                "threat_assessment": {"status": "ACTIVE", "range": "50km"},
                "neural_link": {"status": "STANDBY", "latency": "0.001ms"}
            }
        }
            
    def deploy_suit(self, suit_name, deployment_method="Hall of Armor"):
        """Deploy specified Iron Man suit with advanced checks"""
        try:
            if suit_name in self.active_suits:
                if self.deployment_systems[deployment_method]["status"] != "READY":
                    raise Exception(f"{deployment_method} not ready for deployment")
                
                self.current_suit = suit_name
                self._initialize_suit_systems(suit_name)
                
                # Run pre-flight checks
                checks = self._run_preflight_checks()
                if not all(checks.values()):
                    failed_systems = [k for k, v in checks.items() if not v]
                    raise Exception(f"Pre-flight checks failed for systems: {failed_systems}")
                
                return f"Deploying {suit_name} via {deployment_method}. All systems online."
            return f"Error: {suit_name} not found in database."
        except Exception as e:
            return f"Deployment failed: {str(e)}"
            
    def _initialize_suit_systems(self, suit_name):
        """Initialize all suit systems for deployment"""
        try:
            # Power up sequence
            self.suit_systems["power"]["arc_reactor"]["output"] = 100
            self.suit_systems["power"]["backup_power"]["status"] = "STANDBY"
            
            # Boot up defensive systems
            self.suit_systems["defense"]["shields"]["status"] = "READY"
            self.suit_systems["defense"]["armor_integrity"] = 100
            
            # Initialize weapons
            self.suit_systems["weapons"]["repulsors"]["status"] = "READY"
            self.suit_systems["weapons"]["unibeam"]["status"] = "CHARGING"
            
            # Start flight systems
            self.suit_systems["flight_systems"]["thrusters"]["status"] = "READY"
            self.suit_systems["flight_systems"]["stabilizers"]["status"] = "ACTIVE"
            
            # Boot AI systems
            self.suit_systems["ai_systems"]["targeting"]["status"] = "ACTIVE"
            self.suit_systems["ai_systems"]["neural_link"]["status"] = "INITIALIZING"
            
            return True
        except Exception as e:
            logging.error(f"Suit initialization error: {e}")
            return False
            
    def _run_preflight_checks(self):
        """Run comprehensive pre-flight system checks"""
        checks = {
            "power": self._check_power_systems(),
            "weapons": self._check_weapons_systems(),
            "flight": self._check_flight_systems(),
            "life_support": self._check_life_support(),
            "defense": self._check_defense_systems(),
            "ai": self._check_ai_systems()
        }
        return checks
        
    def _check_power_systems(self):
        """Check power systems status"""
        try:
            arc_reactor = self.suit_systems["power"]["arc_reactor"]
            return arc_reactor["output"] >= 85 and arc_reactor["efficiency"] >= 90
        except Exception as e:
            logging.error(f"Power systems check failed: {e}")
            return False
            
    def _check_weapons_systems(self):
        """Check weapons systems status"""
        try:
            weapons = self.suit_systems["weapons"]
            return (weapons["repulsors"]["status"] == "READY" and
                    weapons["missiles"]["count"] > 0)
        except Exception as e:
            logging.error(f"Weapons systems check failed: {e}")
            return False
            
    def _check_flight_systems(self):
        """Check flight systems status"""
        try:
            flight = self.suit_systems["flight_systems"]
            return (flight["thrusters"]["status"] == "READY" and
                    flight["stabilizers"]["status"] == "ACTIVE")
        except Exception as e:
            logging.error(f"Flight systems check failed: {e}")
            return False
            
    def _check_life_support(self):
        """Check life support systems"""
        try:
            life = self.suit_systems["life_support"]
            return (life["oxygen_levels"] > 90 and
                    life["pressure"] == "NORMAL")
        except Exception as e:
            logging.error(f"Life support check failed: {e}")
            return False
            
    def _check_defense_systems(self):
        """Check defense systems status"""
        try:
            defense = self.suit_systems["defense"]
            return (defense["shields"]["status"] == "READY" and
                    defense["armor_integrity"] > 90)
        except Exception as e:
            logging.error(f"Defense systems check failed: {e}")
            return False
            
    def _check_ai_systems(self):
        """Check AI systems status"""
        try:
            ai = self.suit_systems["ai_systems"]
            return (ai["targeting"]["status"] == "ACTIVE" and
                    ai["threat_assessment"]["status"] == "ACTIVE")
        except Exception as e:
            logging.error(f"AI systems check failed: {e}")
            return False
            
    def _start_suit_monitoring(self):
        """Start suit monitoring in separate thread"""
        try:
            threading.Thread(target=self._monitor_suit_systems, daemon=True).start()
        except Exception as e:
            logging.error(f"Failed to start suit monitoring: {e}")
            
    def _monitor_suit_systems(self):
        """Monitor all suit systems in real-time"""
        while True:
            try:
                if self.current_suit:
                    # Monitor power systems
                    self._monitor_power()
                    
                    # Monitor flight systems
                    self._monitor_flight()
                    
                    # Monitor life support
                    self._monitor_life_support()
                    
                    # Monitor defense systems
                    self._monitor_defense()
                    
                    # Update AI systems
                    self._update_ai_systems()
                    
                time.sleep(0.1)  # 100ms monitoring interval
            except Exception as e:
                logging.error(f"Suit monitoring error: {e}")
                time.sleep(1)
                
    def _monitor_power(self):
        """Monitor power systems"""
        power = self.suit_systems["power"]["arc_reactor"]
        if power["output"] < 50:
            self._trigger_power_warning()
            
    def _monitor_flight(self):
        """Monitor flight systems"""
        flight = self.suit_systems["flight_systems"]
        if flight["thrusters"]["power"] < 60:
            self._trigger_flight_warning()
            
    def _monitor_life_support(self):
        """Monitor life support systems"""
        life = self.suit_systems["life_support"]
        if life["oxygen_levels"] < 80:
            self._trigger_life_support_warning()
            
    def _monitor_defense(self):
        """Monitor defense systems"""
        defense = self.suit_systems["defense"]
        if defense["armor_integrity"] < 70:
            self._trigger_defense_warning()
            
    def _update_ai_systems(self):
        """Update AI systems"""
        ai = self.suit_systems["ai_systems"]
        ai["targeting"]["accuracy"] = min(100, ai["targeting"]["accuracy"] + 0.1)
        
    def _trigger_power_warning(self):
        """Handle power system warnings"""
        logging.warning("Power levels critical")
        self.suit_systems["power"]["backup_power"]["status"] = "ACTIVE"
        
    def _trigger_flight_warning(self):
        """Handle flight system warnings"""
        logging.warning("Flight system power low")
        self.suit_systems["flight_systems"]["navigation"]["mode"] = "EMERGENCY"
        
    def _trigger_life_support_warning(self):
        """Handle life support warnings"""
        logging.warning("Life support levels critical")
        self.suit_systems["life_support"]["pressure"] = "EMERGENCY"
        
    def _trigger_defense_warning(self):
        """Handle defense system warnings"""
        logging.warning("Armor integrity compromised")
        self.suit_systems["defense"]["shields"]["power"] = 100

if __name__ == "__main__":
    try:
        jarvis = JarvisAssistant()
        jarvis.speak("JARVIS Mark 1 online. Arc reactor functioning at optimal levels.")
        
        # Activate workshop mode with error handling
        jarvis.toggle_workshop_mode()
        
        # Deploy a suit with error handling
        try:
            status = jarvis.suit_interface.deploy_suit("Mark III")
            jarvis.speak(status)
        except Exception as e:
            jarvis.logger.error(f"Suit deployment error: {e}")
            jarvis.speak("Suit deployment systems offline")
        
        # Monitor arc reactor
        try:
            reactor_status = jarvis.power_management["current_output"]
            jarvis.speak(f"Arc reactor currently operating at {reactor_status}% capacity")
        except Exception as e:
            jarvis.logger.error(f"Power monitoring error: {e}")
            jarvis.speak("Arc reactor monitoring systems need calibration")
            
        # Start main loop
        jarvis.run()
        
    except Exception as e:
        print(f"Critical system error: {e}")
        if 'jarvis' in locals():
            jarvis.logger.error(f"Critical system error: {e}")
            jarvis.speak("Critical system failure. Initiating emergency shutdown.")