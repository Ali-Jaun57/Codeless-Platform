import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from utils.json_parser import extract_json_from_text
from ..shared.agent_state import AgentState

logger = Logger(__name__)

class UIUX:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        logger.step("Class B UI/UX Agent", "initialized")