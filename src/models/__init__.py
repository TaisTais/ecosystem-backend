from src.models.achievements import Achievement, UserAchievement, ModerationRecord
from src.models.complaints import Complaint
from src.models.events import Event, EventApplicant, EventParticipant, EventOrganizer
from src.models.feed import Post, PostComment, PostLike
from src.models.map import EcoPoint, Status, Review, Visit
from src.models.users import User

# важно: импортировать после всех моделей
from src.models.relationships import *  # noqa: F401,F403
