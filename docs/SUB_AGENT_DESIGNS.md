# Sub-Agent Designs

**Last Updated:** 2026-02-21  
**Status:** Design Complete  
**Target Platform:** RPi5 Host + Client Devices

---

## 1. Overview & Philosophy

The Bodhi is built from **specialized sub-agents** inspired by human brain regions. Each agent has a specific responsibility and communicates via the event bus. This modular design enables:

1. **Parallel processing:** Agents run concurrently
2. **Independent evolution:** Agents can be upgraded individually
3. **Resource management:** Agents can be loaded/unloaded dynamically
4. **Clear responsibilities:** Each agent has a well-defined role

### Agent Roster

**Sensory Agents (Input Processing):**
1. **Visual Agent** - Processes screen content
2. **Auditory Agent** - Processes voice input

**Cognitive Agents (High-Level Processing):**
3. **Language Center** - Natural language understanding and generation
4. **Emotion Regulator** - Tracks and manages emotional state
5. **Skill Executor** - Executes learned skills

**Motor Agents (Output):**
6. **Motor Controller** - Controls character animations
7. **Voice Synthesizer** - Generates speech output

**Utility Agents:**
8. **Memory Manager** - Manages memory consolidation
9. **Tool Coordinator** - Manages tool plugin execution

---

## 2. Visual Agent

### 2.1 Responsibilities

**Primary Function:** Process and understand screen content

**Capabilities:**
- Receive visual insights from client (OCR, object detection, UI elements)
- Maintain current screen context
- Detect notable changes
- Answer visual queries from Central Agent
- Feed screen awareness to memory system

### 2.2 Interface

```python
# visual_agent.py

from typing import Dict, Any, List, Optional
import asyncio

class VisualAgent:
    """
    Visual Agent - Processes screen content.
    
    Inspired by: Visual cortex (V1, V2, V4, IT)
    """
    
    def __init__(
        self,
        event_bus: 'EventBus',
        memory_mgr: 'MemoryManager',
        client_comm: 'ClientCommunicator'
    ):
        self.event_bus = event_bus
        self.memory = memory_mgr
        self.client_comm = client_comm
        
        # Current screen state
        self.current_context: Optional[Dict[str, Any]] = None
        self.last_update_time = None
        
        # Subscribe to events
        self.event_bus.subscribe('screen.insights_received', self.on_screen_insights)
        self.event_bus.subscribe('agent.visual.query', self.on_visual_query)
    
    # ===== Event Handlers =====
    
    async def on_screen_insights(self, insights: Dict[str, Any]):
        """
        Handle screen insights from client.
        
        Called when client sends processed screen data.
        """
        # Update current context
        self.current_context = insights
        self.last_update_time = datetime.utcnow()
        
        # Detect notable changes
        changes = await self._detect_notable_changes(insights)
        
        if changes:
            # Notify Central Agent of interesting changes
            await self.event_bus.publish('visual.notable_change', {
                'changes': changes,
                'context': insights
            })
        
        # Store in memory
        await self._store_visual_memory(insights)
    
    async def on_visual_query(self, query: Dict[str, Any]):
        """
        Handle visual query from Central Agent.
        
        Examples:
        - "What's on the screen?"
        - "How many unread emails?"
        - "What app is active?"
        """
        query_text = query['query']
        query_id = query['id']
        
        # Check if we have current context
        if not self.current_context:
            # Request fresh capture from client
            insights = await self._request_screen_capture()
        else:
            insights = self.current_context
        
        # Answer query based on insights
        answer = await self._answer_visual_query(query_text, insights)
        
        # Return answer
        await self.event_bus.publish('visual.query_response', {
            'query_id': query_id,
            'answer': answer,
            'context': insights
        })
    
    # ===== Core Methods =====
    
    async def _request_screen_capture(
        self,
        mode: str = 'active_window'
    ) -> Dict[str, Any]:
        """Request screen capture from client."""
        response = await self.client_comm.request({
            'type': 'screen_capture',
            'mode': mode
        }, timeout=5.0)
        
        return response
    
    async def _detect_notable_changes(
        self,
        new_insights: Dict[str, Any]
    ) -> List[str]:
        """
        Detect notable changes from previous screen state.
        
        Returns: List of change descriptions
        """
        if not self.current_context:
            return []
        
        changes = []
        
        # Check app change
        old_app = self.current_context.get('app_context', {}).get('app_name')
        new_app = new_insights.get('app_context', {}).get('app_name')
        
        if old_app != new_app:
            changes.append(f"App changed from {old_app} to {new_app}")
        
        # Check for new notifications
        old_notable = set(self.current_context.get('insights', {}).get('notable_items', []))
        new_notable = set(new_insights.get('insights', {}).get('notable_items', []))
        
        added_items = new_notable - old_notable
        if added_items:
            changes.append(f"New items: {', '.join(added_items)}")
        
        # Check for unread count changes (e.g., emails)
        old_unread = self.current_context.get('insights', {}).get('unread_count', 0)
        new_unread = new_insights.get('insights', {}).get('unread_count', 0)
        
        if new_unread > old_unread:
            diff = new_unread - old_unread
            changes.append(f"{diff} new unread item(s)")
        
        return changes
    
    async def _answer_visual_query(
        self,
        query: str,
        insights: Dict[str, Any]
    ) -> str:
        """
        Answer a visual query based on screen insights.
        
        Args:
            query: Natural language query
            insights: Screen insights
        
        Returns:
            Natural language answer
        """
        query_lower = query.lower()
        
        # Pattern matching for common queries
        if 'what' in query_lower and ('screen' in query_lower or 'see' in query_lower):
            # "What's on my screen?"
            app = insights.get('app_context', {}).get('app_name', 'unknown')
            scene = insights.get('scene_type', 'unknown')
            activity = insights.get('activity', 'unknown')
            
            answer = f"You're {activity} in {app}. "
            
            if 'caption' in insights:
                answer += insights['caption']
            else:
                answer += f"It appears to be a {scene} view."
            
            # Add notable items
            notable = insights.get('insights', {}).get('notable_items', [])
            if notable:
                answer += f" I notice: {', '.join(notable[:3])}."
            
            return answer
        
        elif 'how many' in query_lower:
            # Extract what they're asking about
            if 'email' in query_lower or 'message' in query_lower:
                count = insights.get('insights', {}).get('unread_count', 0)
                return f"You have {count} unread emails."
            else:
                return "I can see the screen, but I'm not sure what count you're asking about."
        
        elif 'what app' in query_lower or 'which app' in query_lower:
            app = insights.get('app_context', {}).get('app_name', 'unknown')
            return f"The active app is {app}."
        
        elif 'read' in query_lower:
            # Extract and return text
            text = insights.get('text_content', {}).get('full_text', '')
            if text:
                return text
            else:
                return "I don't see any text on the screen."
        
        else:
            # Generic fallback
            return "I can see the screen, but I'm not sure how to answer that specific question."
    
    async def _store_visual_memory(self, insights: Dict[str, Any]):
        """Store screen event in memory."""
        memory_entry = {
            'type': 'screen_event',
            'timestamp': insights.get('timestamp'),
            'app': insights.get('app_context', {}).get('app_name'),
            'activity': insights.get('activity'),
            'scene': insights.get('scene_type'),
            'text_summary': insights.get('text_content', {}).get('full_text', '')[:500],
            'notable_items': insights.get('insights', {}).get('notable_items', []),
            'importance': self._calculate_importance(insights)
        }
        
        await self.memory.store(memory_entry)
    
    def _calculate_importance(self, insights: Dict[str, Any]) -> float:
        """Calculate importance score for screen event."""
        importance = 0.3  # Base
        
        # Boost for certain apps
        app = insights.get('app_context', {}).get('app_name', '')
        if app in ['email', 'calendar', 'slack', 'teams']:
            importance += 0.2
        
        # Boost for notable items
        if insights.get('insights', {}).get('notable_items'):
            importance += 0.2
        
        # Boost for certain activities
        activity = insights.get('activity', '')
        if activity in ['reading', 'writing', 'coding']:
            importance += 0.1
        
        return min(importance, 1.0)
    
    # ===== State Methods =====
    
    async def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get current screen context."""
        return self.current_context
    
    async def is_screen_idle(self) -> bool:
        """Check if screen hasn't changed recently."""
        if not self.last_update_time:
            return True
        
        elapsed = (datetime.utcnow() - self.last_update_time).total_seconds()
        return elapsed > 30  # 30 seconds of no updates = idle
```

### 2.3 Resource Requirements

- **Memory:** 50 MB
- **CPU:** <5% (just processes JSON, no heavy computation)
- **Dependencies:** None (just data processing)

---

## 3. Auditory Agent

### 3.1 Responsibilities

**Primary Function:** Process and understand voice input

**Capabilities:**
- Receive transcribed text from client STT
- Extract intent and emotion from voice input
- Detect questions vs statements vs commands
- Feed voice input to Central Agent
- Store voice interactions in memory

### 3.2 Interface

```python
# auditory_agent.py

class AuditoryAgent:
    """
    Auditory Agent - Processes voice input.
    
    Inspired by: Auditory cortex (A1, A2, Wernicke's area)
    """
    
    def __init__(
        self,
        event_bus: 'EventBus',
        memory_mgr: 'MemoryManager'
    ):
        self.event_bus = event_bus
        self.memory = memory_mgr
        
        # Subscribe to events
        self.event_bus.subscribe('voice.transcript_received', self.on_transcript)
    
    async def on_transcript(self, data: Dict[str, Any]):
        """
        Handle transcribed voice input from client.
        
        Args:
            data: {
                'transcript': str,
                'confidence': float,
                'timestamp': str
            }
        """
        transcript = data['transcript']
        confidence = data.get('confidence', 1.0)
        
        # Analyze input
        analysis = await self._analyze_voice_input(transcript)
        
        # Store in memory
        await self._store_voice_memory(transcript, analysis)
        
        # Forward to Central Agent
        await self.event_bus.publish('auditory.input_processed', {
            'transcript': transcript,
            'confidence': confidence,
            'analysis': analysis
        })
    
    async def _analyze_voice_input(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze voice input.
        
        Returns:
            {
                'type': 'question' | 'statement' | 'command',
                'intent': str,
                'emotion': str,
                'keywords': List[str]
            }
        """
        # Classify input type
        input_type = self._classify_input_type(transcript)
        
        # Extract keywords
        keywords = await self._extract_keywords(transcript)
        
        # Detect emotional tone (simple heuristics)
        emotion = self._detect_emotion_from_text(transcript)
        
        # Extract intent (simplified)
        intent = await self._extract_intent(transcript)
        
        return {
            'type': input_type,
            'intent': intent,
            'emotion': emotion,
            'keywords': keywords
        }
    
    def _classify_input_type(self, text: str) -> str:
        """Classify if input is question, statement, or command."""
        text_lower = text.lower().strip()
        
        # Questions
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which']
        if any(text_lower.startswith(word) for word in question_words):
            return 'question'
        
        if text.endswith('?'):
            return 'question'
        
        # Commands
        command_verbs = ['show', 'tell', 'open', 'close', 'create', 'delete', 
                        'help', 'find', 'search', 'play', 'stop']
        if any(text_lower.startswith(verb) for verb in command_verbs):
            return 'command'
        
        # Default to statement
        return 'statement'
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction (can be enhanced with NLP)
        import re
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                    'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        return keywords[:5]  # Top 5 keywords
    
    def _detect_emotion_from_text(self, text: str) -> str:
        """Detect emotion from text (simple keyword matching)."""
        text_lower = text.lower()
        
        # Positive
        if any(word in text_lower for word in ['great', 'awesome', 'thanks', 'perfect', 'love']):
            return 'joy'
        
        # Negative
        if any(word in text_lower for word in ['error', 'wrong', 'bad', 'hate', 'terrible']):
            return 'frustration'
        
        # Confusion
        if any(word in text_lower for word in ['confused', 'unclear', 'understand', 'what']):
            return 'confusion'
        
        # Neutral
        return 'neutral'
    
    async def _extract_intent(self, text: str) -> str:
        """Extract user intent (simplified)."""
        text_lower = text.lower()
        
        # Pattern matching for common intents
        if 'email' in text_lower:
            if any(word in text_lower for word in ['check', 'show', 'read']):
                return 'check_email'
            elif 'send' in text_lower or 'write' in text_lower:
                return 'send_email'
        
        if 'screen' in text_lower:
            return 'check_screen'
        
        if 'calendar' in text_lower or 'schedule' in text_lower:
            return 'check_calendar'
        
        # Generic
        return 'general_query'
    
    async def _store_voice_memory(self, transcript: str, analysis: Dict[str, Any]):
        """Store voice interaction in memory."""
        await self.memory.store({
            'type': 'voice_input',
            'timestamp': datetime.utcnow().isoformat(),
            'transcript': transcript,
            'input_type': analysis['type'],
            'intent': analysis['intent'],
            'emotion': analysis['emotion'],
            'importance': 0.7  # Voice input is typically important
        })
```

### 3.3 Resource Requirements

- **Memory:** 40 MB
- **CPU:** <5%
- **Dependencies:** None

---

## 4. Language Center

### 4.1 Responsibilities

**Primary Function:** Natural language understanding and generation

**Capabilities:**
- Intent recognition
- Entity extraction
- Text generation
- Sentiment analysis
- Language translation (future)

### 4.2 Interface

```python
# language_center.py

class LanguageCenter:
    """
    Language Center - NLU and NLG.
    
    Inspired by: Broca's area, Wernicke's area
    """
    
    def __init__(
        self,
        event_bus: 'EventBus',
        model_path: str = 'models/distilbert-tiny'
    ):
        self.event_bus = event_bus
        
        # Load models
        self.nlu_model = self._load_nlu_model(model_path)
        self.nlg_model = None  # Optional for generation
        
        # Subscribe to events
        self.event_bus.subscribe('language.intent_request', self.on_intent_request)
        self.event_bus.subscribe('language.generate_request', self.on_generate_request)
    
    def _load_nlu_model(self, path: str):
        """Load NLU model for intent recognition."""
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        tokenizer = AutoTokenizer.from_pretrained(path)
        model = AutoModelForSequenceClassification.from_pretrained(path)
        
        return {'tokenizer': tokenizer, 'model': model}
    
    async def on_intent_request(self, data: Dict[str, Any]):
        """
        Handle intent recognition request.
        
        Args:
            data: {
                'text': str,
                'request_id': str
            }
        """
        text = data['text']
        request_id = data['request_id']
        
        # Recognize intent
        intent = await self.recognize_intent(text)
        
        # Extract entities
        entities = await self.extract_entities(text)
        
        # Sentiment
        sentiment = await self.analyze_sentiment(text)
        
        # Publish result
        await self.event_bus.publish('language.intent_response', {
            'request_id': request_id,
            'intent': intent,
            'entities': entities,
            'sentiment': sentiment
        })
    
    async def recognize_intent(self, text: str) -> Dict[str, Any]:
        """
        Recognize user intent from text.
        
        Returns:
            {
                'intent': str,
                'confidence': float
            }
        """
        # Encode text
        tokenizer = self.nlu_model['tokenizer']
        model = self.nlu_model['model']
        
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=128)
        
        # Inference
        import torch
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
        
        # Get top prediction
        intent_idx = torch.argmax(probs).item()
        confidence = probs[0][intent_idx].item()
        
        # Map index to intent name
        intent_names = [
            'greeting', 'farewell', 'question', 'command',
            'information_request', 'task_request', 'acknowledgment'
        ]
        intent = intent_names[intent_idx] if intent_idx < len(intent_names) else 'unknown'
        
        return {
            'intent': intent,
            'confidence': confidence
        }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Returns: List of {'entity': str, 'type': str, 'position': int}
        """
        # Simplified entity extraction (can use spaCy or similar)
        import re
        
        entities = []
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({'entity': email, 'type': 'email', 'position': text.index(email)})
        
        # Extract dates (simplified)
        dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
        for date in dates:
            entities.append({'entity': date, 'type': 'date', 'position': text.index(date)})
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\b', text)
        for number in numbers:
            entities.append({'entity': number, 'type': 'number', 'position': text.index(number)})
        
        return entities
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Returns: {'positive': float, 'negative': float, 'neutral': float}
        """
        # Simple keyword-based sentiment (can use transformer model)
        positive_words = ['good', 'great', 'excellent', 'happy', 'love', 'perfect']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'wrong', 'error']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count + 1  # Avoid division by zero
        
        return {
            'positive': pos_count / total,
            'negative': neg_count / total,
            'neutral': 1.0 - (pos_count + neg_count) / total
        }
    
    async def on_generate_request(self, data: Dict[str, Any]):
        """
        Handle text generation request.
        
        Args:
            data: {
                'prompt': str,
                'max_length': int,
                'request_id': str
            }
        """
        prompt = data['prompt']
        max_length = data.get('max_length', 100)
        request_id = data['request_id']
        
        # Generate text
        generated = await self.generate_text(prompt, max_length)
        
        # Publish result
        await self.event_bus.publish('language.generate_response', {
            'request_id': request_id,
            'text': generated
        })
    
    async def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """Generate text from prompt (optional feature)."""
        # This would use GPT-2 or similar
        # For now, simple template-based generation
        
        return f"Based on your request: {prompt}, here is my response."
```

### 4.3 Resource Requirements

- **Memory:** 150 MB (DistilBERT-tiny + runtime)
- **CPU:** 20-30% during inference (brief)
- **Dependencies:** transformers, torch

---

## 5. Emotion Regulator

### 5.1 Responsibilities

**Primary Function:** Track and manage emotional state

**Capabilities:**
- Maintain current emotional state
- Update emotions based on events
- Smooth emotional transitions
- Influence animation and voice
- Store emotional history

### 5.2 Interface

```python
# emotion_regulator.py

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class EmotionalState:
    """Represents current emotional state."""
    primary_emotion: str  # 'joy', 'sadness', 'anger', etc.
    intensity: float  # 0.0-1.0
    valence: float  # -1.0 (negative) to 1.0 (positive)
    arousal: float  # 0.0 (calm) to 1.0 (excited)
    timestamp: datetime


class EmotionRegulator:
    """
    Emotion Regulator - Manages emotional state.
    
    Inspired by: Amygdala, prefrontal cortex
    """
    
    def __init__(self, event_bus: 'EventBus'):
        self.event_bus = event_bus
        
        # Current emotional state
        self.current_state = EmotionalState(
            primary_emotion='neutral',
            intensity=0.5,
            valence=0.0,
            arousal=0.3,
            timestamp=datetime.utcnow()
        )
        
        # Emotional history (for smoothing)
        self.history: List[EmotionalState] = []
        
        # Subscribe to emotion-triggering events
        self.event_bus.subscribe('task.completed', self.on_task_completed)
        self.event_bus.subscribe('task.failed', self.on_task_failed)
        self.event_bus.subscribe('user.praise', self.on_user_praise)
        self.event_bus.subscribe('user.frustration', self.on_user_frustration)
        self.event_bus.subscribe('system.error', self.on_system_error)
    
    # ===== Event Handlers (Emotion Triggers) =====
    
    async def on_task_completed(self, data: Dict[str, Any]):
        """Task completed successfully → Joy/Satisfaction."""
        await self.update_emotion('joy', intensity=0.7, duration=5.0)
    
    async def on_task_failed(self, data: Dict[str, Any]):
        """Task failed → Worry/Sadness."""
        await self.update_emotion('worry', intensity=0.6, duration=10.0)
    
    async def on_user_praise(self, data: Dict[str, Any]):
        """User praised companion → Joy/Pride."""
        await self.update_emotion('joy', intensity=0.9, duration=15.0)
    
    async def on_user_frustration(self, data: Dict[str, Any]):
        """User is frustrated → Concern/Worry."""
        await self.update_emotion('concern', intensity=0.7, duration=10.0)
    
    async def on_system_error(self, data: Dict[str, Any]):
        """System error occurred → Worry."""
        await self.update_emotion('worry', intensity=0.5, duration=5.0)
    
    # ===== Core Methods =====
    
    async def update_emotion(
        self,
        emotion: str,
        intensity: float,
        duration: float = 5.0
    ):
        """
        Update emotional state.
        
        Args:
            emotion: Emotion name
            intensity: 0.0-1.0
            duration: How long this emotion lasts (seconds)
        """
        # Map emotion to valence/arousal
        emotion_map = {
            'joy': {'valence': 0.8, 'arousal': 0.7},
            'sadness': {'valence': -0.6, 'arousal': 0.2},
            'anger': {'valence': -0.7, 'arousal': 0.9},
            'fear': {'valence': -0.8, 'arousal': 0.8},
            'surprise': {'valence': 0.0, 'arousal': 0.9},
            'disgust': {'valence': -0.6, 'arousal': 0.5},
            'neutral': {'valence': 0.0, 'arousal': 0.3},
            'excitement': {'valence': 0.9, 'arousal': 0.95},
            'worry': {'valence': -0.4, 'arousal': 0.6},
            'concern': {'valence': -0.3, 'arousal': 0.5},
            'confusion': {'valence': -0.2, 'arousal': 0.4},
        }
        
        emotion_dims = emotion_map.get(emotion, emotion_map['neutral'])
        
        # Create new state
        new_state = EmotionalState(
            primary_emotion=emotion,
            intensity=intensity,
            valence=emotion_dims['valence'],
            arousal=emotion_dims['arousal'],
            timestamp=datetime.utcnow()
        )
        
        # Smooth transition from current state
        self.current_state = await self._smooth_transition(
            self.current_state,
            new_state,
            blend_factor=0.7  # 70% new, 30% old
        )
        
        # Add to history
        self.history.append(self.current_state)
        
        # Publish emotion change
        await self.event_bus.publish('emotion.changed', {
            'emotion': emotion,
            'intensity': intensity,
            'valence': self.current_state.valence,
            'arousal': self.current_state.arousal
        })
        
        # Schedule decay back to neutral
        asyncio.create_task(self._decay_emotion(duration))
    
    async def _smooth_transition(
        self,
        old_state: EmotionalState,
        new_state: EmotionalState,
        blend_factor: float
    ) -> EmotionalState:
        """Smooth transition between emotional states."""
        blended = EmotionalState(
            primary_emotion=new_state.primary_emotion,
            intensity=blend_factor * new_state.intensity + (1 - blend_factor) * old_state.intensity,
            valence=blend_factor * new_state.valence + (1 - blend_factor) * old_state.valence,
            arousal=blend_factor * new_state.arousal + (1 - blend_factor) * old_state.arousal,
            timestamp=datetime.utcnow()
        )
        return blended
    
    async def _decay_emotion(self, duration: float):
        """Gradually decay emotion back to neutral."""
        await asyncio.sleep(duration)
        
        # Decay towards neutral
        await self.update_emotion('neutral', intensity=0.5, duration=0)
    
    # ===== Getters =====
    
    def get_current_emotion(self) -> str:
        """Get current primary emotion."""
        return self.current_state.primary_emotion
    
    def get_emotion_intensity(self) -> float:
        """Get current emotion intensity."""
        return self.current_state.intensity
    
    def get_valence(self) -> float:
        """Get current emotional valence (-1 to 1)."""
        return self.current_state.valence
    
    def get_arousal(self) -> float:
        """Get current arousal level (0 to 1)."""
        return self.current_state.arousal
    
    def get_state(self) -> EmotionalState:
        """Get complete emotional state."""
        return self.current_state
```

### 5.3 Resource Requirements

- **Memory:** 30 MB
- **CPU:** <1%
- **Dependencies:** None

---

## 6. Remaining Agents (Brief Specifications)

### 6.1 Skill Executor

**Already designed in:** `SKILL_TREE_DESIGN.md`

**Key Methods:**
- `execute_skill(skill_id, params)` - Execute a skill
- `get_skill_competency(skill_id)` - Get skill level
- `list_skills()` - List available skills

**Resources:** 200 MB RAM, 10-30% CPU during execution

### 6.2 Motor Controller

**Already designed in:** `CHARACTER_ANIMATION_SYSTEM.md`

**Key Methods:**
- `express_emotion(emotion, intensity)` - Show emotion
- `point_at(x, y)` - Point at UI element
- `speak(text, phonemes)` - Speak with lip-sync
- `react_to_activity(activity)` - Activity-aware animations

**Resources:** 30 MB RAM, <5% CPU

### 6.3 Voice Synthesizer

**Already designed in:** `VOICE_PIPELINE.md`

**Key Methods:**
- `synthesize(text, emotion, intensity)` - Generate speech
- `select_voice(personality)` - Choose voice
- `apply_prosody(text, emotion)` - Add natural intonation

**Resources:** 100-180 MB RAM, 30-50% CPU during synthesis

### 6.4 Memory Manager

**Already designed in:** `MEMORY_CONSOLIDATION_DESIGN.md`

**Key Methods:**
- `store(memory_entry)` - Store new memory
- `retrieve(query, limit)` - Search memories
- `consolidate()` - Run consolidation pass
- `forget(importance_threshold)` - Probabilistic forgetting

**Resources:** 200 MB RAM, 10-20% CPU during consolidation

### 6.5 Tool Coordinator

**Already designed in:** `TOOL_PLUGIN_SYSTEM.md`

**Key Methods:**
- `execute_tool(tool_id, capability, params)` - Execute tool
- `check_permission(tool_id, capability)` - Check permission
- `request_user_approval(tool_id, action)` - Ask user

**Resources:** 80 MB RAM, 5-15% CPU during tool execution

---

## 7. Agent Communication Patterns

### 7.1 Event Bus

All agents communicate via event bus (Redis Pub/Sub):

```python
# event_bus.py

class EventBus:
    """Central event bus for agent communication."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.subscribers = {}  # topic -> [callbacks]
    
    async def publish(self, topic: str, data: Dict[str, Any]):
        """Publish event to topic."""
        message = json.dumps(data)
        await self.redis.publish(topic, message)
    
    def subscribe(self, topic: str, callback):
        """Subscribe to topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        
        # Start listener if not already running
        asyncio.create_task(self._listen(topic))
    
    async def _listen(self, topic: str):
        """Listen for messages on topic."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(topic)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                
                # Call all subscribers
                for callback in self.subscribers.get(topic, []):
                    await callback(data)
```

### 7.2 Common Event Topics

```
# User input events
user.text_input           → Central Agent
user.voice_input          → Auditory Agent
user.screen_query         → Visual Agent

# Agent processing events
visual.insights_received  → Visual Agent
visual.notable_change     → Central Agent
auditory.input_processed  → Central Agent
language.intent_response  → Central Agent
emotion.changed           → Motor Controller, Voice Synthesizer

# Task events
task.started              → All agents (context)
task.completed            → Emotion Regulator (trigger joy)
task.failed               → Emotion Regulator (trigger worry)
task.progress             → Central Agent

# System events
system.error              → Emotion Regulator, Central Agent
system.memory_pressure    → Module Activation Manager
system.power_state_changed→ Module Activation Manager
```

---

## 8. Agent Lifecycle

### 8.1 Initialization Order

```
1. Event Bus (Redis connection)
2. Memory Manager (database connections)
3. Emotion Regulator (base state)
4. Language Center (load models)
5. Visual Agent
6. Auditory Agent
7. Skill Executor
8. Tool Coordinator
9. Motor Controller
10. Voice Synthesizer
11. Central Agent (orchestrator)
```

### 8.2 Shutdown Sequence

```
1. Central Agent (stop processing new inputs)
2. Motor Controller (finish animations)
3. Voice Synthesizer (finish speech)
4. Tool Coordinator (cancel pending tools)
5. Skill Executor (save state)
6. Visual/Auditory Agents (disconnect)
7. Language Center (unload models)
8. Emotion Regulator (save history)
9. Memory Manager (flush to disk)
10. Event Bus (close connections)
```

---

## 9. Summary

### Agent Summary Table

| Agent | Memory | CPU (Idle) | CPU (Active) | Location | Key Role |
|-------|--------|------------|--------------|----------|----------|
| Visual Agent | 50 MB | <5% | <5% | Host | Screen understanding |
| Auditory Agent | 40 MB | <5% | <5% | Host | Voice input processing |
| Language Center | 150 MB | <1% | 20-30% | Host | NLU/NLG |
| Emotion Regulator | 30 MB | <1% | <1% | Host | Emotional state |
| Skill Executor | 200 MB | 5% | 10-30% | Host | Execute skills |
| Motor Controller | 30 MB | <5% | <5% | Host | Animation commands |
| Voice Synthesizer | 100-180 MB | <1% | 30-50% | Host | TTS |
| Memory Manager | 200 MB | 5% | 10-20% | Host | Memory system |
| Tool Coordinator | 80 MB | <5% | 5-15% | Host | Tool execution |
| **Total** | **~880-960 MB** | **~25%** | **varies** | - | - |

### Integration Complete ✅

All agents are:
- ✅ Clearly defined with responsibilities
- ✅ Event-driven communication
- ✅ Independently loadable/unloadable
- ✅ Resource-constrained for RPi5
- ✅ Fully integrated with existing systems

---

**Design Status:** ✅ COMPLETE  
**Ready for:** Final system integration design  
**Estimated Implementation Time:** 6-8 weeks for all agents
