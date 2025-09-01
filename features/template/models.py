"""
[FEATURE_NAME] Domain Models

title: [FEATURE_NAME] Domain Models
purpose: Define core entities and value objects for [FEATURE_NAME] feature
inputs: []
outputs: [{"name": "domain_entities", "type": "classes"}]
effects: ["domain_model_definitions"]
deps: ["pydantic", "typing"]
owners: ["backend-team"]
stability: wip
since_version: "0.1.0"
complexity: low
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

# Value Objects
@dataclass(frozen=True)
class [FeatureName]Id:
    """Strongly-typed ID for [FEATURE_NAME] entities."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Invalid [FeatureName]Id")
    
    @classmethod
    def generate(cls) -> '[FeatureName]Id':
        """Generate a new unique ID."""
        return cls(value=str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class [FeatureName]Status:
    """Status value object with validation."""
    value: str
    
    VALID_STATUSES = ["active", "inactive", "pending", "archived"]
    
    def __post_init__(self):
        if self.value not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.value}")
    
    @classmethod
    def active(cls) -> '[FeatureName]Status':
        return cls(value="active")
    
    @classmethod
    def inactive(cls) -> '[FeatureName]Status':
        return cls(value="inactive")


# Domain Entities
@dataclass
class [FeatureName]Entity:
    """
    Core [FEATURE_NAME] domain entity.
    
    Represents the main business concept for this feature.
    Contains business rules and invariants.
    """
    id: [FeatureName]Id
    name: str
    status: [FeatureName]Status
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self._validate()
    
    def _validate(self) -> None:
        """Validate entity invariants."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Entity name cannot be empty")
        
        if len(self.name) > 255:
            raise ValueError("Entity name too long")
        
        if self.updated_at and self.updated_at < self.created_at:
            raise ValueError("Updated time cannot be before created time")
    
    def update_name(self, new_name: str) -> '[FeatureName]Entity':
        """Update entity name with validation."""
        updated = dataclass.replace(
            self,
            name=new_name.strip(),
            updated_at=datetime.utcnow()
        )
        updated._validate()
        return updated
    
    def activate(self) -> '[FeatureName]Entity':
        """Activate this entity."""
        return dataclass.replace(
            self,
            status=[FeatureName]Status.active(),
            updated_at=datetime.utcnow()
        )
    
    def deactivate(self) -> '[FeatureName]Entity':
        """Deactivate this entity.""" 
        return dataclass.replace(
            self,
            status=[FeatureName]Status.inactive(),
            updated_at=datetime.utcnow()
        )
    
    def is_active(self) -> bool:
        """Check if entity is active."""
        return self.status.value == "active"


# Domain Events (if needed)
@dataclass(frozen=True)
class [FeatureName]Created:
    """Domain event: [FEATURE_NAME] was created."""
    entity_id: [FeatureName]Id
    entity_name: str
    occurred_at: datetime
    
    @classmethod
    def from_entity(cls, entity: [FeatureName]Entity) -> '[FeatureName]Created':
        return cls(
            entity_id=entity.id,
            entity_name=entity.name,
            occurred_at=datetime.utcnow()
        )


@dataclass(frozen=True)
class [FeatureName]Updated:
    """Domain event: [FEATURE_NAME] was updated."""
    entity_id: [FeatureName]Id
    old_name: str
    new_name: str
    occurred_at: datetime


# Factory Functions
def create_[feature_name]_entity(name: str) -> [FeatureName]Entity:
    """Factory function to create a new [FEATURE_NAME] entity."""
    return [FeatureName]Entity(
        id=[FeatureName]Id.generate(),
        name=name.strip(),
        status=[FeatureName]Status.active(),
        created_at=datetime.utcnow(),
        metadata={}
    )