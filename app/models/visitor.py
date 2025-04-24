from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Visitor:
    tenant_id: str
    first_name: str
    last_name: str
    email: str
    visit_date: datetime
    phone: Optional[str] = None
    visitor_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert visitor object to dictionary"""
        return {
            'visitor_id': self.visitor_id,
            'tenant_id': self.tenant_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'visit_date': self.visit_date.isoformat(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Visitor':
        """Create visitor object from dictionary"""
        return cls(
            visitor_id=data.get('visitor_id'),
            tenant_id=data['tenant_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone'),
            visit_date=datetime.fromisoformat(data['visit_date']),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        ) 