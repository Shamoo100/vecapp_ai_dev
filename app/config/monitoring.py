from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import start_http_server
from typing import Dict, Any

class MonitoringService:
    def __init__(self):
        # Set up tracing
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__)

        # Set up metrics
        reader = PrometheusMetricReader()
        self.meter_provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(self.meter_provider)
        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self.visitor_counter = self.meter.create_counter(
            "visitors_total",
            description="Total number of visitors"
        )
        
        self.follow_up_histogram = self.meter.create_histogram(
            "follow_up_duration_seconds",
            description="Time taken for follow-ups"
        )
        
        self.engagement_gauge = self.meter.create_gauge(
            "engagement_score",
            description="Current engagement score"
        )

    def start_prometheus_server(self, port: int = 8000):
        """Start Prometheus metrics server"""
        start_http_server(port)

    async def track_visitor(self, tenant_id: str):
        """Track new visitor"""
        self.visitor_counter.add(1, {"tenant_id": tenant_id})

    async def track_follow_up(self, duration: float, tenant_id: str):
        """Track follow-up duration"""
        self.follow_up_histogram.record(
            duration,
            {"tenant_id": tenant_id}
        )

    async def update_engagement_score(self, score: float, tenant_id: str):
        """Update engagement score"""
        self.engagement_gauge.set(score, {"tenant_id": tenant_id})

    async def create_span(self, name: str, attributes: Dict[str, Any]):
        """Create tracing span"""
        return self.tracer.start_as_current_span(
            name,
            attributes=attributes
        ) 