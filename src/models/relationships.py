from sqlalchemy import and_
from sqlalchemy.orm import foreign

from src.models.users import User
from src.models.feed import Post
from src.models.events import Event
from src.models.complaints import Complaint

# User <-> Complaint
User.complaints_received.property.primaryjoin = and_(
    User.id == foreign(Complaint.target_id),
    Complaint.target_type == "user",
)

Complaint.users.property.primaryjoin = and_(
    User.id == foreign(Complaint.target_id),
    Complaint.target_type == "user",
)

# Post <-> Complaint
Post.complaints.property.primaryjoin = and_(
    Post.id == foreign(Complaint.target_id),
    Complaint.target_type == "post",
)

Complaint.posts.property.primaryjoin = and_(
    Post.id == foreign(Complaint.target_id),
    Complaint.target_type == "post",
)

# Event <-> Complaint
Event.complaints.property.primaryjoin = and_(
    Event.id == foreign(Complaint.target_id),
    Complaint.target_type == "event",
)

Complaint.events.property.primaryjoin = and_(
    Event.id == foreign(Complaint.target_id),
    Complaint.target_type == "event",
)
