# JARVIS Personal Assistant

JARVIS is a voice-controlled personal assistant designed to help with everyday tasks, media control, workshop assistance, and more. Inspired by Tony Stark's AI assistant from Iron Man, this Python-based application uses speech recognition, text-to-speech, and various integrations for a comprehensive assistant experience.

## Features

- **Voice-activated commands**: Interact with JARVIS using natural speech
- **Media control**: Play music, adjust volume, control media playback
- **Workshop mode**: Specialized environment for focused work with real-time system monitoring
- **Social media monitoring**: Get trending topics and news headlines
- **Research assistance**: Quick Wikipedia lookups and web searches
- **Productivity tools**: Timers, pomodoro technique, focus mode, note-taking
- **System management**: PC control (sleep, restart, shutdown), file operations
- **Dynamic memory**: Remembers conversations and preferences
- **Self-improvement**: Can learn and improve itself over time

## Requirements

- Python 3.8+
- Microphone for voice input
- Speakers for voice output
- Ollama (optional, for enhanced AI capabilities)

## Installation

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure API keys in the `jarvis_config.yaml` file (optional)
4. Run JARVIS:
   ```
   python main.py
   ```

## Configuration

Customize JARVIS through the `jarvis_config.yaml` file:

- Sound effects
- Voice settings
- Workshop mode thresholds
- Social media settings
- News API integration
- Memory management

## Voice Commands

JARVIS responds to a wide range of commands, including:

- "What time is it?"
- "Play [song name] on YouTube"
- "Set volume to 50"
- "Enter workshop mode"
- "Tell me about [topic]"
- "Set a timer for 30 minutes"
- "What's trending on social media?"
- "Tell me the news"

Check the help command for a full list of available commands.

## License

See the LICENSE file for details.

## Acknowledgments

- Built using various open-source libraries
- Inspired by Iron Man's JARVIS AI assistant
