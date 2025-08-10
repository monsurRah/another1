"""
Production-grade microservice for SRE assessment
Handles data analysis with graceful shutdown capabilities
"""

import asyncio
import json
import logging
import signal
import statistics
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from pydantic import BaseModel, Field, field_validator

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}'
)
logger = logging.getLogger(__name__)

# Create a custom registry to avoid conflicts
registry = CollectorRegistry()

# Prometheus metrics with custom registry
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status'],
    registry=registry
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'HTTP request duration', 
    ['method', 'endpoint'],
    registry=registry
)
ERROR_COUNT = Counter(
    'http_errors_total', 
    'Total HTTP errors', 
    ['endpoint', 'error_type'],
    registry=registry
)

class PayloadRequest(BaseModel):
    """Request model for payload endpoint with validation"""
    numbers: List[Union[int, float]] = Field(..., description="List of numbers for statistical analysis")
    text: str = Field(..., description="Text for analysis", min_length=1)
    
    @field_validator('numbers')
    @classmethod
    def validate_numbers(cls, v):
        if not v:
            raise ValueError("Numbers array cannot be empty")
        if len(v) > 10000:  # Prevent DoS attacks
            raise ValueError("Numbers array too large (max 10000 items)")
        return v
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if len(v) > 50000:  # Prevent DoS attacks
            raise ValueError("Text too long (max 50000 characters)")
        return v

class PayloadResponse(BaseModel):
    """Response model for payload endpoint"""
    numeric_analysis: Dict[str, float]
    text_analysis: Dict[str, int]
    processing_time_ms: float

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str

class GracefulShutdown:
    """Handles graceful shutdown with in-flight request tracking"""
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.active_requests = 0
        self.accepting_requests = True
        
    def start_request(self):
        """Track start of request processing"""
        if not self.accepting_requests:
            raise HTTPException(status_code=503, detail="Service is shutting down")
        self.active_requests += 1
        logger.info(f"Active requests: {self.active_requests}")
        
    def end_request(self):
        """Track end of request processing"""
        self.active_requests -= 1
        logger.info(f"Active requests: {self.active_requests}")
        
    async def shutdown(self):
        """Initiate graceful shutdown"""
        logger.info("Initiating graceful shutdown...")
        self.accepting_requests = False
        
        # Wait for all active requests to complete
        while self.active_requests > 0:
            logger.info(f"Waiting for {self.active_requests} active requests to complete...")
            await asyncio.sleep(0.1)
            
        logger.info("All requests completed. Shutdown complete.")
        self.shutdown_event.set()

# Global shutdown handler
shutdown_handler = GracefulShutdown()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting SRE Microservice...")
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(shutdown_handler.shutdown())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    yield
    
    # Shutdown
    await shutdown_handler.shutdown()
    logger.info("SRE Microservice stopped.")

# Initialize FastAPI application
app = FastAPI(
    title="SRE Microservice Assessment",
    description="Production-grade microservice for data analysis with graceful shutdown",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Middleware for request tracking and metrics"""
    start_time = time.time()
    
    # Track request start
    shutdown_handler.start_request()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        logger.info(f"Request processed: {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
        
        return response
        
    except Exception as e:
        ERROR_COUNT.labels(
            endpoint=request.url.path,
            error_type=type(e).__name__
        ).inc()
        logger.error(f"Request error: {request.method} {request.url.path} - {str(e)}")
        raise
    finally:
        # Track request end
        shutdown_handler.end_request()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        version="1.0.0"
    )

@app.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint"""
    if not shutdown_handler.accepting_requests:
        raise HTTPException(status_code=503, detail="Service not ready")
        
    return HealthResponse(
        status="ready",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        version="1.0.0"
    )

def calculate_statistics(numbers: List[Union[int, float]]) -> Dict[str, float]:
    """Calculate statistical metrics from numbers array"""
    try:
        return {
            "minimum": float(min(numbers)),
            "maximum": float(max(numbers)),
            "mean": float(statistics.mean(numbers)),
            "median": float(statistics.median(numbers)),
            "standard_deviation": float(statistics.stdev(numbers)) if len(numbers) > 1 else 0.0,
            "count": len(numbers)
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error calculating statistics")

def analyze_text(text: str) -> Dict[str, int]:
    """Analyze text for word and character counts"""
    try:
        words = text.split()
        return {
            "word_count": len(words),
            "character_count": len(text),
            "character_count_no_spaces": len(text.replace(" ", "")),
            "sentence_count": len([s for s in text.split('.') if s.strip()]),
            "paragraph_count": len([p for p in text.split('\n') if p.strip()])
        }
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing text")

@app.post("/payload", response_model=PayloadResponse)
async def process_payload(payload: PayloadRequest):
    """Process payload with numeric and text analysis"""
    start_time = time.time()
    
    logger.info(f"Processing payload: {len(payload.numbers)} numbers, {len(payload.text)} characters")
    
    try:
        # Perform analyses asynchronously where applicable
        numeric_task = asyncio.create_task(
            asyncio.get_event_loop().run_in_executor(None, calculate_statistics, payload.numbers)
        )
        text_task = asyncio.create_task(
            asyncio.get_event_loop().run_in_executor(None, analyze_text, payload.text)
        )
        
        numeric_analysis, text_analysis = await asyncio.gather(numeric_task, text_task)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        logger.info(f"Payload processed successfully in {processing_time:.2f}ms")
        
        return PayloadResponse(
            numeric_analysis=numeric_analysis,
            text_analysis=text_analysis,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error processing payload: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Expose Prometheus metrics"""
    return generate_latest(registry)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )