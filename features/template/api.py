"""
[FEATURE_NAME] API Layer

title: [FEATURE_NAME] HTTP API
purpose: Expose [FEATURE_NAME] operations via REST endpoints
inputs: [{"name": "http_requests", "type": "HTTP"}]
outputs: [{"name": "json_responses", "type": "HTTP"}]  
effects: ["http_responses", "service_calls", "logging"]
deps: ["service", "models", "fastapi"]
owners: ["backend-team"]
stability: wip
since_version: "0.1.0"
complexity: low
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from .models import [FeatureName]Entity, [FeatureName]Id
from .service import [FeatureName]Service, Create[FeatureName]Command, Update[FeatureName]Command

# Structured logging
logger = structlog.get_logger(__name__)

# API Router
router = APIRouter(prefix="/[feature-name]", tags=["[feature-name]"])


# Request/Response Models
class Create[FeatureName]Request(BaseModel):
    """Request model for creating [FEATURE_NAME]."""
    name: str = Field(..., min_length=1, max_length=255, description="[FEATURE_NAME] name")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()


class Update[FeatureName]Request(BaseModel):
    """Request model for updating [FEATURE_NAME]."""
    name: str = Field(..., min_length=1, max_length=255, description="New [FEATURE_NAME] name")
    
    @validator('name') 
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()


class [FeatureName]Response(BaseModel):
    """Response model for [FEATURE_NAME] entity."""
    id: str = Field(..., description="Unique [FEATURE_NAME] identifier")
    name: str = Field(..., description="[FEATURE_NAME] name")
    status: str = Field(..., description="[FEATURE_NAME] status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @classmethod
    def from_entity(cls, entity: [FeatureName]Entity) -> '[FeatureName]Response':
        """Convert domain entity to API response."""
        return cls(
            id=str(entity.id),
            name=entity.name,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    request_id: str = Field(..., description="Request identifier")


# Dependency injection (adjust based on your DI setup)
async def get_[feature_name]_service() -> [FeatureName]Service:
    """
    Dependency to get [FEATURE_NAME] service instance.
    
    TODO: Replace with actual DI container setup
    """
    # This is a placeholder - implement actual dependency injection
    from .wiring import get_[feature_name]_service
    return get_[feature_name]_service()


def get_request_id(request: Request) -> str:
    """Extract or generate request ID for tracing."""
    return request.headers.get("X-Request-ID", f"req-{datetime.utcnow().timestamp()}")


def get_tenant_id(request: Request) -> str:
    """Extract tenant ID from request."""
    # TODO: Implement actual tenant extraction logic
    return request.headers.get("X-Tenant-ID", "default")


# API Endpoints
@router.post("/", response_model=[FeatureName]Response, status_code=201)
async def create_[feature_name](
    request_data: Create[FeatureName]Request,
    request: Request,
    service: [FeatureName]Service = Depends(get_[feature_name]_service)
) -> [FeatureName]Response:
    """
    Create a new [FEATURE_NAME].
    
    **Business Rules:**
    - Name must be unique across all [FEATURE_NAME]s
    - Name cannot be empty or only whitespace
    - Created [FEATURE_NAME] starts as active
    
    **Returns:**
    - 201: [FEATURE_NAME] created successfully
    - 400: Invalid input data
    - 409: [FEATURE_NAME] with same name already exists
    """
    request_id = get_request_id(request)
    tenant_id = get_tenant_id(request)
    
    logger.info(
        "api_create_[feature_name]_started",
        name=request_data.name,
        request_id=request_id,
        tenant_id=tenant_id
    )
    
    try:
        # Create command
        command = Create[FeatureName]Command(
            name=request_data.name,
            request_id=request_id,
            tenant_id=tenant_id
        )
        
        # Execute business logic
        result = await service.create_[feature_name](command)
        
        if not result.success:
            # Determine appropriate HTTP status code
            if "already exists" in result.error_message:
                status_code = 409  # Conflict
                error_code = "DUPLICATE_NAME"
            else:
                status_code = 400  # Bad Request
                error_code = "INVALID_INPUT"
            
            logger.warning(
                "api_create_[feature_name]_failed",
                error=result.error_message,
                error_code=error_code,
                request_id=request_id
            )
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": result.error_message,
                    "code": error_code,
                    "request_id": request_id
                }
            )
        
        # Success response
        response = [FeatureName]Response.from_entity(result.entity)
        
        logger.info(
            "api_create_[feature_name]_success",
            entity_id=response.id,
            name=response.name,
            request_id=request_id
        )
        
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(
            "api_create_[feature_name]_error",
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR", 
                "request_id": request_id
            }
        )


@router.get("/{entity_id}", response_model=[FeatureName]Response)
async def get_[feature_name](
    entity_id: str,
    request: Request,
    service: [FeatureName]Service = Depends(get_[feature_name]_service)
) -> [FeatureName]Response:
    """
    Get [FEATURE_NAME] by ID.
    
    **Returns:**
    - 200: [FEATURE_NAME] found
    - 404: [FEATURE_NAME] not found
    """
    request_id = get_request_id(request)
    
    logger.debug(
        "api_get_[feature_name]_started",
        entity_id=entity_id,
        request_id=request_id
    )
    
    try:
        # Validate and convert ID
        [feature_name]_id = [FeatureName]Id(entity_id)
        
        # Get entity
        entity = await service.get_[feature_name]_by_id([feature_name]_id, request_id)
        
        if not entity:
            logger.info(
                "api_get_[feature_name]_not_found",
                entity_id=entity_id,
                request_id=request_id
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"[FEATURE_NAME] not found: {entity_id}",
                    "code": "NOT_FOUND",
                    "request_id": request_id
                }
            )
        
        response = [FeatureName]Response.from_entity(entity)
        
        logger.debug(
            "api_get_[feature_name]_success",
            entity_id=entity_id,
            name=response.name,
            request_id=request_id
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "api_get_[feature_name]_invalid_id",
            entity_id=entity_id,
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid [FEATURE_NAME] ID: {entity_id}",
                "code": "INVALID_ID",
                "request_id": request_id
            }
        )
    except Exception as e:
        logger.error(
            "api_get_[feature_name]_error",
            entity_id=entity_id,
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "request_id": request_id
            }
        )


@router.put("/{entity_id}", response_model=[FeatureName]Response)
async def update_[feature_name](
    entity_id: str,
    request_data: Update[FeatureName]Request,
    request: Request,
    service: [FeatureName]Service = Depends(get_[feature_name]_service)
) -> [FeatureName]Response:
    """
    Update existing [FEATURE_NAME].
    
    **Business Rules:**
    - [FEATURE_NAME] must exist
    - New name must be unique (if changed)
    
    **Returns:**
    - 200: [FEATURE_NAME] updated successfully  
    - 400: Invalid input data
    - 404: [FEATURE_NAME] not found
    - 409: Name conflict with existing [FEATURE_NAME]
    """
    request_id = get_request_id(request)
    tenant_id = get_tenant_id(request)
    
    logger.info(
        "api_update_[feature_name]_started",
        entity_id=entity_id,
        new_name=request_data.name,
        request_id=request_id
    )
    
    try:
        # Validate and convert ID
        [feature_name]_id = [FeatureName]Id(entity_id)
        
        # Create command
        command = Update[FeatureName]Command(
            entity_id=[feature_name]_id,
            new_name=request_data.name,
            request_id=request_id,
            tenant_id=tenant_id
        )
        
        # Execute business logic
        result = await service.update_[feature_name](command)
        
        if not result.success:
            # Determine appropriate HTTP status code
            if "not found" in result.error_message:
                status_code = 404  # Not Found
                error_code = "NOT_FOUND"
            elif "already exists" in result.error_message:
                status_code = 409  # Conflict
                error_code = "DUPLICATE_NAME"
            else:
                status_code = 400  # Bad Request
                error_code = "INVALID_INPUT"
            
            logger.warning(
                "api_update_[feature_name]_failed",
                entity_id=entity_id,
                error=result.error_message,
                error_code=error_code,
                request_id=request_id
            )
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": result.error_message,
                    "code": error_code,
                    "request_id": request_id
                }
            )
        
        # Success response
        response = [FeatureName]Response.from_entity(result.entity)
        
        logger.info(
            "api_update_[feature_name]_success",
            entity_id=entity_id,
            old_name="[logged_in_service]",
            new_name=response.name,
            request_id=request_id
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "api_update_[feature_name]_invalid_id",
            entity_id=entity_id,
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid [FEATURE_NAME] ID: {entity_id}",
                "code": "INVALID_ID",
                "request_id": request_id
            }
        )
    except Exception as e:
        logger.error(
            "api_update_[feature_name]_error",
            entity_id=entity_id,
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "request_id": request_id
            }
        )


@router.get("/", response_model=List[[FeatureName]Response])
async def list_[feature_name]s(
    request: Request,
    active_only: bool = True,
    service: [FeatureName]Service = Depends(get_[feature_name]_service)
) -> List[[FeatureName]Response]:
    """
    List [FEATURE_NAME] entities.
    
    **Query Parameters:**
    - active_only: If true, only return active [FEATURE_NAME]s (default: true)
    
    **Returns:**
    - 200: List of [FEATURE_NAME] entities (may be empty)
    """
    request_id = get_request_id(request)
    
    logger.debug(
        "api_list_[feature_name]s_started", 
        active_only=active_only,
        request_id=request_id
    )
    
    try:
        if active_only:
            entities = await service.list_active_[feature_name]s(request_id)
        else:
            # TODO: Implement list_all if needed
            entities = await service.list_active_[feature_name]s(request_id)
        
        responses = [[FeatureName]Response.from_entity(entity) for entity in entities]
        
        logger.debug(
            "api_list_[feature_name]s_success",
            count=len(responses),
            active_only=active_only,
            request_id=request_id
        )
        
        return responses
        
    except Exception as e:
        logger.error(
            "api_list_[feature_name]s_error",
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "request_id": request_id
            }
        )


@router.post("/{entity_id}/activate", response_model=[FeatureName]Response)
async def activate_[feature_name](
    entity_id: str,
    request: Request,
    service: [FeatureName]Service = Depends(get_[feature_name]_service)  
) -> [FeatureName]Response:
    """
    Activate [FEATURE_NAME].
    
    **Returns:**
    - 200: [FEATURE_NAME] activated (or was already active)
    - 404: [FEATURE_NAME] not found
    """
    request_id = get_request_id(request)
    
    logger.info(
        "api_activate_[feature_name]_started",
        entity_id=entity_id,
        request_id=request_id
    )
    
    try:
        # Validate and convert ID
        [feature_name]_id = [FeatureName]Id(entity_id)
        
        # Execute business logic
        result = await service.activate_[feature_name]([feature_name]_id, request_id)
        
        if not result.success:
            if "not found" in result.error_message:
                status_code = 404
                error_code = "NOT_FOUND"
            else:
                status_code = 400
                error_code = "INVALID_INPUT"
            
            logger.warning(
                "api_activate_[feature_name]_failed",
                entity_id=entity_id,
                error=result.error_message,
                request_id=request_id
            )
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": result.error_message,
                    "code": error_code,
                    "request_id": request_id
                }
            )
        
        response = [FeatureName]Response.from_entity(result.entity)
        
        logger.info(
            "api_activate_[feature_name]_success",
            entity_id=entity_id,
            request_id=request_id
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "api_activate_[feature_name]_invalid_id",
            entity_id=entity_id,
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid [FEATURE_NAME] ID: {entity_id}",
                "code": "INVALID_ID", 
                "request_id": request_id
            }
        )
    except Exception as e:
        logger.error(
            "api_activate_[feature_name]_error",
            entity_id=entity_id,
            error=str(e),
            request_id=request_id
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "request_id": request_id
            }
        )