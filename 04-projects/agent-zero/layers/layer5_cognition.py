"""
Agent Zero - Layer 5: Cognition (Base-of-Self-Aware-AI)
Multi-tier memory: WorkingMemory (session) + LongTermMemory (SQLite) + UserProfile.
"""
import sqlite3, json, re
from datetime import datetime
from collections import deque
from typing import Any

class WorkingMemory:
    def __init__(self, max_size=20):
        self.buffer = deque(maxlen=max_size)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    def add(self, user_input, intent, response, confidence=1.0):
        self.buffer.append({"session_id": self.session_id,
            "timestamp": datetime.now().isoformat(), "user_input": user_input,
            "intent": intent, "response": response, "confidence": confidence})
    def recent(self, n=5): return list(self.buffer)[-n:]

class LongTermMemory:
    def __init__(self, db_path="agent_zero_memory.db"):
        self.db_path = db_path
        conn = sqlite3.connect(db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
            timestamp TEXT, user_input TEXT, intent TEXT,
            confidence REAL, response TEXT, context TEXT)""")
        conn.commit(); conn.close()
    def store(self, session_id, user_input, intent, response, confidence=1.0, context=None):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO conversations (session_id,timestamp,user_input,intent,confidence,response,context) VALUES (?,?,?,?,?,?,?)",
            (session_id, datetime.now().isoformat(), user_input, intent, confidence, response, json.dumps(context or {})))
        conn.commit(); conn.close()
    def recall(self, query, limit=5):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT user_input,intent,response,timestamp FROM conversations WHERE user_input LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit)).fetchall()
        conn.close()
        return [{"input": r[0], "intent": r[1], "response": r[2], "time": r[3]} for r in rows]
    def total_turns(self):
        conn = sqlite3.connect(self.db_path)
        n = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        conn.close(); return n

class UserProfile:
    def __init__(self, db_path="agent_zero_memory.db"):
        self.db_path = db_path
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS user_profile (key TEXT PRIMARY KEY, value TEXT, updated TEXT)")
        conn.commit(); conn.close()
    def set(self, key, value):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR REPLACE INTO user_profile (key,value,updated) VALUES (?,?,?)",
            (key, json.dumps(value), datetime.now().isoformat()))
        conn.commit(); conn.close()
    def get(self, key, default=None):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT value FROM user_profile WHERE key=?", (key,)).fetchone()
        conn.close(); return json.loads(row[0]) if row else default
    def summary(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT key,value FROM user_profile").fetchall()
        conn.close(); return {r[0]: json.loads(r[1]) for r in rows}

class CognitionCore:
    def __init__(self, db_path="agent_zero_memory.db"):
        self.working = WorkingMemory()
        self.longterm = LongTermMemory(db_path)
        self.profile = UserProfile(db_path)
    def process(self, user_input, intent, response, confidence=1.0):
        self.working.add(user_input, intent, response, confidence)
        self.longterm.store(self.working.session_id, user_input, intent, response,
            confidence, context=self.profile.summary())
        self._detect_name(user_input)
    def _detect_name(self, text):
        for pat in [r"my name is ([A-Z][a-z]+)", r"i am ([A-Z][a-z]+)", r"call me ([A-Z][a-z]+)"]:
            m = re.search(pat, text, re.IGNORECASE)
            if m: self.profile.set("user_name", m.group(1)); break
    def context_for(self, query):
        return {"recent": self.working.recent(5),
                "relevant": self.longterm.recall(query, limit=3),
                "profile": self.profile.summary(),
                "total_turns": self.longterm.total_turns()}
    def status(self):
        name = self.profile.get("user_name", "Unknown")
        return f"User: {name} | Total turns: {self.longterm.total_turns()} | Session: {len(self.working.buffer)}"
