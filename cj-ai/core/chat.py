from database.database import Database
from core.knowledge_loader import KnowledgeEntry, load_knowledge
from core.search import KnowledgeSearch
from core.memory import SessionMemory
from core.learning import LearningModule
from core.security_filter import is_cybersecurity_related, out_of_scope_reply
from core.shell_helper import extract_command_name, has_command_reference, build_command_response
from utils.logger import get_logger
from utils.helpers import is_arabic
import config

logger = get_logger()

NO_ANSWER_EN = (
    "I don't have a confident answer for that question in my knowledge base.\n"
    "Your question has been recorded for future review, so we can improve CJ-AI.\n\n"
    "Tip: Try rephrasing your question, or ask about a specific tool or concept."
)

NO_ANSWER_AR = (
    "لا أملك إجابة مؤكدة لهذا السؤال في قاعدة معرفتي حالياً.\n"
    "تم تسجيل سؤالك للمراجعة اللاحقة من قِبل المطورين لتحسين CJ-AI.\n\n"
    "تلميح: حاول إعادة صياغة سؤالك، أو اسأل عن أداة أو مفهوم محدد."
)


class ChatEngine:
    def __init__(self, db: Database, user_id: int):
        self.db = db
        self.user_id = user_id
        self.memory = SessionMemory()
        self.learner = LearningModule(db)
        self._entries = load_knowledge(config.KNOWLEDGE_FILE)
        self.searcher = KnowledgeSearch(self._entries)

    def reload_knowledge(self):
        self._entries = load_knowledge(config.KNOWLEDGE_FILE)
        self.searcher.reload(self._entries)

    def respond(self, user_input: str) -> str:
        user_input = user_input.strip()

        # Save user message to DB and memory
        self.db.save_message(self.user_id, "user", user_input)
        self.memory.add("user", user_input)

        response = self._generate_response(user_input)

        # Save assistant response
        self.db.save_message(self.user_id, "assistant", response)
        self.memory.add("assistant", response)

        return response

    def _generate_response(self, text: str) -> str:
        # 1. Shell command check — always try this first for tool-specific queries
        command = extract_command_name(text)
        if command and has_command_reference(command):
            result = build_command_response(command)
            if result:
                return result

        # 2. Knowledge base search — answer if we have a good match regardless of filter
        entry = self.searcher.find_best(text)
        if entry:
            return entry.answer

        # 3. Scope check — only reject after confirming we have nothing useful to say
        if not is_cybersecurity_related(text):
            logger.info("Out of scope question: %s", text[:60])
            return out_of_scope_reply(text)

        # 4. In-scope but no answer found — record and inform user
        self.learner.record_unanswered(self.user_id, text)
        arabic = is_arabic(text)
        return NO_ANSWER_AR if arabic else NO_ANSWER_EN
