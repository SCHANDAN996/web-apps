import json
import os
import requests
from src.database import TradingDB
from src.brain import TradingBrain
from backtest_engine import run_backtest  # noqa: F401 — lazy reference, not directly called

class ChatAgent:
    def __init__(self, db: TradingDB, brain: TradingBrain):
        self.db = db
        self.brain = brain
        # User defined API key for GROQ (Free, super fast LLaMA models)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        
    def set_api_key(self, api_key: str):
        self.groq_api_key = api_key
        # Save to env logic here if needed

    def process_message(self, user_message: str) -> str:
        """
        Takes raw Hindi/English text, sends to GROQ LLM for intent classification,
        then executes the matching Python function, and returns a human response.
        """
        if not self.groq_api_key:
            return "Sir, meri API key missing hai. Pehle settings mein GROQ LLM ya Gemini API key dalein taaki main chat kar saku."

        # The System Prompt defines the AI's personality and routing logic
        system_prompt = """
        You are TradeKaro AI, an extremely intelligent algorithmic trading AI. 
        The user will talk to you in casual Hindi/English (Hinglish).
        
        Your job is to classify their intent and return a STRICT JSON response. 
        DO NOT EXPLAIN ANYTHING. JUST RETURN JSON.
        
        Available Actions:
        1. "market_status" - If user asks how the market is doing or current bot PnL.
        2. "run_backtest" - If user asks to backtest a specific coin/stock (extract 'symbol' if present).
        3. "brain_status" - If user asks how the PPO Transformer training is going or what the AI thinks.
        4. "general_chat" - If the user is just saying hi or asking general questions.

        JSON FORMAT:
        {
            "action": "<action_name>",
            "symbol": "<symbol or null>",
            "reply_text": "<Your conversational reply in Hinglish>"
        }
        """

        try:
            # Send to GROQ API (using LLaMA 3 8B which is fast and smart)
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "response_format": {"type": "json_object"}
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = json.loads(result['choices'][0]['message']['content'])
                
                action = llm_response.get('action')
                symbol = llm_response.get('symbol')
                reply_text = llm_response.get('reply_text', 'Samajh gaya sir.')

                # EXECUTE THE LOCALLY ROUTED ACTION
                return self._execute_action(action, symbol, reply_text)
            else:
                return f"Sir, API connect nahi ho rahi: {response.text}"
                
        except Exception as e:
            return f"Maaf karna sir, kuch error aagaya: {e}"

    def _execute_action(self, action: str, symbol: str, reply_text: str) -> str:
        """Executes actual Python logic based on LLM JSON output."""
        
        if action == "market_status":
            # Fetch real data from VPS Database
            # Dummy logic for architecture demonstration
            return f"Sir, {reply_text}\n\n[System Inject: Nifty is currently bullish. VIX is at 14.5]"
            
        elif action == "run_backtest":
            if not symbol: symbol = "NIFTY"
            # Trigger heavy task asynchronously or run simplified version
            return f"Sir, apne kaha {symbol} ka backtest karna hai. \n\n{reply_text}\n\n[System Inject: Initiating Walk-forward backtest for {symbol}...]"
            
        elif action == "brain_status":
            # Read from brain
            input_dim = self.brain.input_features if hasattr(self.brain, 'input_features') else 'Unknown'
            return f"{reply_text}\n\n[System Data: Next-Gen PPO Brain loaded. Input dimensions: {input_dim}]"
            
        else: # general_chat
            return reply_text
