"""
[FEATURE_NAME] Application Service

title: [FEATURE_NAME] Application Service  
purpose: Orchestrate business operations and coordinate between layers
inputs: [{"name": "commands", "type": "command_objects"}]
outputs: [{"name": "results", "type": "result_objects"}]
effects: ["database_changes", "domain_events", "external_api_calls"]
deps: ["models", "repository", "typing"]
owners: ["backend-team"]
stability: wip
since_version: "0.1.0"
complexity: medium
"""

from typing import Optional, List, Protocol
from datetime import datetime
import structlog
from .models import [FeatureName]Entity, [FeatureName]Id, create_[feature_name]_entity

# Structured logging
logger = structlog.get_logger(__name__)


# Repository Protocol (port)
@runtime_checkable
class [FeatureName]Repository(Protocol):
    """Repository interface for [FEATURE_NAME] entities."""
    
    async def save(self, entity: [FeatureName]Entity) -> [FeatureName]Entity:
        """Save entity and return saved version."""
        ...
    
    async def find_by_id(self, entity_id: [FeatureName]Id) -> Optional[[FeatureName]Entity]:
        """Find entity by ID."""
        ...
    
    async def find_by_name(self, name: str) -> Optional[[FeatureName]Entity]:
        """Find entity by name."""
        ...
    
    async def find_active(self) -> List[[FeatureName]Entity]:
        """Find all active entities."""
        ...
    
    async def delete(self, entity_id: [FeatureName]Id) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        ...


# Command/Result Objects
@dataclass
class Create[FeatureName]Command:
    """Command to create a new [FEATURE_NAME]."""
    name: str
    request_id: str = ""
    tenant_id: str = ""

@dataclass  
class Update[FeatureName]Command:
    """Command to update existing [FEATURE_NAME]."""
    entity_id: [FeatureName]Id
    new_name: str
    request_id: str = ""
    tenant_id: str = ""

@dataclass
class [FeatureName]Result:
    """Result of [FEATURE_NAME] operations."""
    success: bool
    entity: Optional[[FeatureName]Entity] = None
    error_message: str = ""
    
    @classmethod
    def success_with_entity(cls, entity: [FeatureName]Entity) -> '[FeatureName]Result':
        return cls(success=True, entity=entity)
    
    @classmethod
    def failure(cls, error: str) -> '[FeatureName]Result':
        return cls(success=False, error_message=error)


# Application Service
class [FeatureName]Service:
    """
    Application service for [FEATURE_NAME] operations.
    
    Coordinates between domain layer and infrastructure.
    Handles business workflows and use cases.
    """
    
    def __init__(self, repository: [FeatureName]Repository):
        self.repository = repository
        self.logger = structlog.get_logger(__name__)
    
    async def create_[feature_name](self, command: Create[FeatureName]Command) -> [FeatureName]Result:
        """
        Create a new [FEATURE_NAME] entity.
        
        Business rules:
        - Name must be unique
        - Name cannot be empty
        - Entity starts as active
        """
        self.logger.info(
            "creating_[feature_name]",
            name=command.name,
            request_id=command.request_id,
            tenant_id=command.tenant_id
        )
        
        try:
            # Check for duplicate name
            existing = await self.repository.find_by_name(command.name)
            if existing:
                error_msg = f"[FEATURE_NAME] with name '{command.name}' already exists"
                self.logger.warning(
                    "[feature_name]_creation_failed",
                    reason="duplicate_name",
                    name=command.name,
                    request_id=command.request_id
                )
                return [FeatureName]Result.failure(error_msg)
            
            # Create entity using factory
            entity = create_[feature_name]_entity(command.name)
            
            # Save to repository
            saved_entity = await self.repository.save(entity)
            
            # Log success
            self.logger.info(
                "[feature_name]_created",
                entity_id=str(saved_entity.id),
                name=saved_entity.name,
                request_id=command.request_id
            )
            
            return [FeatureName]Result.success_with_entity(saved_entity)
            
        except Exception as e:
            error_msg = f"Failed to create [FEATURE_NAME]: {str(e)}"
            self.logger.error(
                "[feature_name]_creation_error",
                error=str(e),
                name=command.name,
                request_id=command.request_id
            )
            return [FeatureName]Result.failure(error_msg)
    
    async def update_[feature_name](self, command: Update[FeatureName]Command) -> [FeatureName]Result:
        """
        Update an existing [FEATURE_NAME] entity.
        
        Business rules:
        - Entity must exist
        - New name must be unique (if changed)
        """
        self.logger.info(
            "updating_[feature_name]",
            entity_id=str(command.entity_id),
            new_name=command.new_name,
            request_id=command.request_id
        )
        
        try:
            # Find existing entity
            entity = await self.repository.find_by_id(command.entity_id)
            if not entity:
                error_msg = f"[FEATURE_NAME] not found: {command.entity_id}"
                self.logger.warning(
                    "[feature_name]_update_failed",
                    reason="not_found",
                    entity_id=str(command.entity_id),
                    request_id=command.request_id
                )
                return [FeatureName]Result.failure(error_msg)
            
            # Check if name is changing and if new name is unique
            if entity.name != command.new_name:
                existing_with_name = await self.repository.find_by_name(command.new_name)
                if existing_with_name and existing_with_name.id != entity.id:
                    error_msg = f"[FEATURE_NAME] with name '{command.new_name}' already exists"
                    self.logger.warning(
                        "[feature_name]_update_failed", 
                        reason="duplicate_name",
                        new_name=command.new_name,
                        request_id=command.request_id
                    )
                    return [FeatureName]Result.failure(error_msg)
            
            # Update entity
            old_name = entity.name
            updated_entity = entity.update_name(command.new_name)
            
            # Save updated entity
            saved_entity = await self.repository.save(updated_entity)
            
            # Log success
            self.logger.info(
                "[feature_name]_updated",
                entity_id=str(saved_entity.id),
                old_name=old_name,
                new_name=saved_entity.name,
                request_id=command.request_id
            )
            
            return [FeatureName]Result.success_with_entity(saved_entity)
            
        except Exception as e:
            error_msg = f"Failed to update [FEATURE_NAME]: {str(e)}"
            self.logger.error(
                "[feature_name]_update_error",
                error=str(e),
                entity_id=str(command.entity_id),
                request_id=command.request_id
            )
            return [FeatureName]Result.failure(error_msg)
    
    async def get_[feature_name]_by_id(self, entity_id: [FeatureName]Id, request_id: str = "") -> Optional[[FeatureName]Entity]:
        """Get [FEATURE_NAME] by ID."""
        self.logger.debug(
            "getting_[feature_name]_by_id",
            entity_id=str(entity_id),
            request_id=request_id
        )
        
        try:
            return await self.repository.find_by_id(entity_id)
        except Exception as e:
            self.logger.error(
                "[feature_name]_get_error",
                error=str(e),
                entity_id=str(entity_id),
                request_id=request_id
            )
            return None
    
    async def list_active_[feature_name]s(self, request_id: str = "") -> List[[FeatureName]Entity]:
        """List all active [FEATURE_NAME] entities."""
        self.logger.debug("listing_active_[feature_name]s", request_id=request_id)
        
        try:
            return await self.repository.find_active()
        except Exception as e:
            self.logger.error(
                "[feature_name]_list_error",
                error=str(e),
                request_id=request_id
            )
            return []
    
    async def activate_[feature_name](self, entity_id: [FeatureName]Id, request_id: str = "") -> [FeatureName]Result:
        """Activate a [FEATURE_NAME] entity."""
        self.logger.info(
            "activating_[feature_name]",
            entity_id=str(entity_id),
            request_id=request_id
        )
        
        try:
            entity = await self.repository.find_by_id(entity_id)
            if not entity:
                return [FeatureName]Result.failure("Entity not found")
            
            if entity.is_active():
                return [FeatureName]Result.success_with_entity(entity)
            
            activated_entity = entity.activate()
            saved_entity = await self.repository.save(activated_entity)
            
            self.logger.info(
                "[feature_name]_activated",
                entity_id=str(saved_entity.id),
                request_id=request_id
            )
            
            return [FeatureName]Result.success_with_entity(saved_entity)
            
        except Exception as e:
            error_msg = f"Failed to activate [FEATURE_NAME]: {str(e)}"
            self.logger.error(
                "[feature_name]_activation_error",
                error=str(e),
                entity_id=str(entity_id),
                request_id=request_id
            )
            return [FeatureName]Result.failure(error_msg)