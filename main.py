import pyttsx3
import datetime
import ollama
import webbrowser
import subprocess
import psutil
import wikipedia
import logging
import asyncio
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from queue import Queue
from threading import Lock

class JarvisAssistant:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Initialize Vosk model
        try:
            self.model = Model(model_path="vosk-model-en-us")
            self.recognizer = KaldiRecognizer(self.model, 16000)
        except Exception as e:
            logging.error(f"Failed to initialize Vosk model: {e}")
            raise

        self.engine_lock = Lock()
        self.audio_queue = Queue()
        
        self.response_cache = {}
        self.user_name = "Sir"
        self.assistant_name = "Jarvis"
        self.voice_type = "male"
        self.voice_speed = 180

        self.common_responses = {
            "hello": "Hello, sir. How may I assist you?",
            "goodbye": "Goodbye, sir. Have a great day.",
            "thank you": "You're welcome, sir.",
            "system status": self.get_system_stats,
            "time": self.get_time,
            "date": self.get_date,
        }

        self.engine = self._initialize_engine()
        self.speak("Jarvis online.")

    def _initialize_engine(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id if self.voice_type == "male" else voices[1].id)
        engine.setProperty('rate', self.voice_speed)
        return engine

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            logging.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))

    def speak(self, text: str) -> None:
        with self.engine_lock:
            self.engine.say(text)
            print(text)
            self.engine.runAndWait()

    async def listen_async(self) -> str:
        """Asynchronously listen for voice input using Vosk"""
        try:
            stream = sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            )

            with stream:
                logging.info("Listening...")
                self.recognizer.Reset()
                
                while True:
                    data = await asyncio.get_event_loop().run_in_executor(
                        None, self.audio_queue.get)
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        if result.get("text", ""):
                            text = result["text"].lower()
                            logging.info(f"{self.user_name}: {text}")
                            return text
                    
                    # Check partial results for better responsiveness
                    partial = json.loads(self.recognizer.PartialResult())
                    if partial.get("partial"):
                        # You can add logic here to handle partial results if needed
                        pass

        except Exception as e:
            logging.error(f"Error in listen_async: {e}")
            self.speak("Error with speech recognition.")
            return ""

    async def get_ai_response_async(self, prompt: str) -> str:
        cache_key = prompt.strip().lower()
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]

        try:
            # Create the messages list
            messages = [
                {
                    'role': 'system',
                    'content': 'You are Jarvis AI assistant. You are working for Mr. Hassan Alnomani, an ambitious young man who made you to help him on his journey like how Jarvis helps Tony Stark.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Use asyncio.to_thread for the synchronous Ollama call
            response = await asyncio.to_thread(
                ollama.chat,
                #model= 'tinyllama',  
                model='llama3.2:1b-instruct-q5_0',
                messages=messages
            )
            
            result = response['message']['content']
            self.response_cache[cache_key] = result
            return result
        except Exception as e:
            logging.error(f"Error in AI response: {e}")
            return f"Error processing request: {str(e)}"

    def get_time(self) -> str:
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self) -> str:
        return datetime.datetime.now().strftime("%B %d, %Y")

    def get_system_stats(self) -> str:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return f"CPU: {cpu}%, Memory: {memory}%, Disk: {disk}%"

    async def process_command(self, command: str) -> None:
        if not command:
            return

        cmd_key = next((key for key in self.common_responses if key in command), None)
        if cmd_key:
            response = self.common_responses[cmd_key]
            if callable(response):
                self.speak(response())
            else:
                self.speak(response)
            return

        if "open" in command:
            if "browser" in command:
                webbrowser.open('http://google.com')
                self.speak("Opening browser")
                return
            elif "notepad" in command:
                subprocess.Popen(["notepad.exe"])
                self.speak("Opening notepad")
                return

        if "search wikipedia" in command:
            query = command.replace("search wikipedia", "").strip()
            try:
                result = wikipedia.summary(query, sentences=1)
                self.speak(result)
            except:
                self.speak("Could not find that information.")
            return

        if "reminder" in command:
            parts = command.split("reminder")
            if len(parts) > 1:
                reminder_text = parts[1].strip()
                self.speak(f"Reminder set for: {reminder_text}")
            return

        response = await self.get_ai_response_async(command)
        self.speak(response)

    async def run(self):
        self.speak("Ready for commands.")

        while True:
            command = await self.listen_async()

            if command:
                if any(phrase in command for phrase in ["shutdown", "goodbye", "exit"]):
                    self.speak("Shutting down.")
                    break

                await self.process_command(command)

async def main():
    jarvis = JarvisAssistant()
    await jarvis.run()

if __name__ == "__main__":
    asyncio.run(main())