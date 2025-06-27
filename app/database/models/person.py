from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean
from app.database.models.base import Base

class Person(Base):
    __tablename__ = 'person'
    
    #id = Column(uuid4, primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    church_branch_id = Column(Integer, index=True)
    user_type_id = Column(Integer, index=True)
    fam_id = Column(Integer, index=True)
    bulk_upload_history_id = Column(Integer)
    
    # Personal Information
    title = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    middle_name = Column(String)
    maiden_name = Column(String)
    gender = Column(String)
    dob = Column(String)
    marital_status = Column(String)
    race = Column(String)
    
    # Contact Information
    email = Column(String)
    country_code = Column(String)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    zip = Column(String)
    landmark = Column(String)
    
    # Account Details
    username = Column(String)
    profile_pic_url = Column(String)
    fcm_token = Column(String)
    timezone = Column(String)
    preferred_comm_method = Column(String)
    
    # Church Related
    member_status = Column(String)
    ministry_department = Column(String)
    advert_team = Column(String)
    volunteer_type = Column(String)
    baptism_location = Column(String)
    baptism_date = Column(String)
    conversion_date = Column(String)
    membership_date = Column(String)
    join_date = Column(String)
    how_join = Column(String)
    joined_via = Column(String)
    
    # Education & Employment
    highest_qualification = Column(String)
    school = Column(String)
    course = Column(String)
    employment_status = Column(String)
    employer = Column(String)
    profession = Column(String)
    industry = Column(String)
    job_title = Column(String)
    grade = Column(String)
    
    # Status Flags
    visibility = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    has_account = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    is_volunteer = Column(Boolean, default=False)
    is_graduated = Column(Boolean, default=False)
    is_flag = Column(Boolean, default=False)
    is_adult = Column(Boolean, default=False)
    is_logout = Column(Boolean, default=False)
    is_deactivated = Column(Boolean, default=False)
    first_time_login = Column(Boolean, default=True)
    is_archive = Column(Boolean, default=False)
    notification_active = Column(Boolean, default=True)
    just_relocated = Column(Boolean, default=False)
    consider_joining = Column(Boolean, default=False)
    import_status = Column(Boolean, default=False)
    registration_link_status = Column(Boolean, default=False)
    resend_link = Column(Boolean, default=False)
    
    # Additional Information
    social_links = Column(String)
    bio = Column(String)
    relationship = Column(String)
    family_status = Column(String)
    login_status = Column(String)
    prayer_request = Column(String)
    daily_devotional = Column(String)
    feedback = Column(String)
    deactivated_reason = Column(String)
    time_to_contact = Column(String)
    joining_our_church = Column(String)
    spiritual_need = Column(String)
    spiritual_challenge = Column(String)
    email_fail_reason = Column(String)
    
    # Timestamps
    family_date_added = Column(String)
    last_login = Column(String)
    session_expiry = Column(String)
    invited_on = Column(String)
    deleted_at = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
