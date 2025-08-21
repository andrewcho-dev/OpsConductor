#!/usr/bin/env python3
"""
RabbitMQ setup script for OpsConductor microservices
Creates exchanges, queues, and bindings for event-driven architecture
"""

import pika
import logging
import sys
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQSetup:
    """Setup RabbitMQ exchanges, queues, and bindings"""
    
    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            sys.exit(1)
    
    def setup_exchanges(self):
        """Create exchanges for different event types"""
        exchanges = [
            {
                'name': 'opsconductor.events',
                'type': 'topic',
                'durable': True,
                'description': 'Main events exchange for all services'
            },
            {
                'name': 'opsconductor.auth',
                'type': 'topic',
                'durable': True,
                'description': 'Authentication and authorization events'
            },
            {
                'name': 'opsconductor.jobs',
                'type': 'topic',
                'durable': True,
                'description': 'Job management and execution events'
            },
            {
                'name': 'opsconductor.system',
                'type': 'topic',
                'durable': True,
                'description': 'System health and monitoring events'
            },
            {
                'name': 'opsconductor.dlx',
                'type': 'direct',
                'durable': True,
                'description': 'Dead letter exchange for failed messages'
            }
        ]
        
        for exchange in exchanges:
            self.channel.exchange_declare(
                exchange=exchange['name'],
                exchange_type=exchange['type'],
                durable=exchange['durable']
            )
            logger.info(f"Created exchange: {exchange['name']} ({exchange['description']})")
    
    def setup_queues(self):
        """Create queues for each service"""
        queues = [
            # Auth Service Queues
            {
                'name': 'auth-service.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'auth-service.failed'
                }
            },
            
            # User Service Queues
            {
                'name': 'user-service.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'user-service.failed'
                }
            },
            
            # Universal Targets Service Queues
            {
                'name': 'universal-targets.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'universal-targets.failed'
                }
            },
            
            # Job Management Service Queues
            {
                'name': 'job-management.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'job-management.failed'
                }
            },
            
            # Job Execution Service Queues
            {
                'name': 'job-execution.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'job-execution.failed'
                }
            },
            {
                'name': 'job-execution.tasks',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'job-execution.tasks.failed'
                }
            },
            
            # Job Scheduling Service Queues
            {
                'name': 'job-scheduling.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'job-scheduling.failed'
                }
            },
            
            # Audit Events Service Queues
            {
                'name': 'audit-events.events',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'audit-events.failed'
                }
            },
            
            # System Monitoring Queues
            {
                'name': 'system.health-checks',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'system.health-checks.failed'
                }
            },
            {
                'name': 'system.alerts',
                'durable': True,
                'arguments': {
                    'x-dead-letter-exchange': 'opsconductor.dlx',
                    'x-dead-letter-routing-key': 'system.alerts.failed'
                }
            },
            
            # Dead Letter Queues
            {
                'name': 'dlq.auth-service',
                'durable': True
            },
            {
                'name': 'dlq.user-service',
                'durable': True
            },
            {
                'name': 'dlq.universal-targets',
                'durable': True
            },
            {
                'name': 'dlq.job-management',
                'durable': True
            },
            {
                'name': 'dlq.job-execution',
                'durable': True
            },
            {
                'name': 'dlq.job-scheduling',
                'durable': True
            },
            {
                'name': 'dlq.audit-events',
                'durable': True
            }
        ]
        
        for queue in queues:
            self.channel.queue_declare(
                queue=queue['name'],
                durable=queue['durable'],
                arguments=queue.get('arguments', {})
            )
            logger.info(f"Created queue: {queue['name']}")
    
    def setup_bindings(self):
        """Create bindings between exchanges and queues"""
        bindings = [
            # Authentication Events
            {
                'exchange': 'opsconductor.auth',
                'queue': 'auth-service.events',
                'routing_key': 'auth.#'
            },
            {
                'exchange': 'opsconductor.auth',
                'queue': 'audit-events.events',
                'routing_key': 'auth.#'
            },
            
            # User Management Events
            {
                'exchange': 'opsconductor.events',
                'queue': 'user-service.events',
                'routing_key': 'user.#'
            },
            {
                'exchange': 'opsconductor.events',
                'queue': 'audit-events.events',
                'routing_key': 'user.#'
            },
            
            # Universal Targets Events
            {
                'exchange': 'opsconductor.events',
                'queue': 'universal-targets.events',
                'routing_key': 'target.#'
            },
            {
                'exchange': 'opsconductor.events',
                'queue': 'job-management.events',
                'routing_key': 'target.#'
            },
            {
                'exchange': 'opsconductor.events',
                'queue': 'job-execution.events',
                'routing_key': 'target.#'
            },
            {
                'exchange': 'opsconductor.events',
                'queue': 'audit-events.events',
                'routing_key': 'target.#'
            },
            
            # Job Management Events
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-management.events',
                'routing_key': 'job.#'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-execution.events',
                'routing_key': 'job.#'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-scheduling.events',
                'routing_key': 'job.#'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'audit-events.events',
                'routing_key': 'job.#'
            },
            
            # Job Execution Events
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-execution.events',
                'routing_key': 'execution.#'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-management.events',
                'routing_key': 'execution.#'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'audit-events.events',
                'routing_key': 'execution.#'
            },
            
            # Job Scheduling Events
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-scheduling.events',
                'routing_key': 'schedule.#'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'job-execution.events',
                'routing_key': 'schedule.triggered'
            },
            {
                'exchange': 'opsconductor.jobs',
                'queue': 'audit-events.events',
                'routing_key': 'schedule.#'
            },
            
            # System Events
            {
                'exchange': 'opsconductor.system',
                'queue': 'system.health-checks',
                'routing_key': 'service.health.#'
            },
            {
                'exchange': 'opsconductor.system',
                'queue': 'system.alerts',
                'routing_key': 'system.alert'
            },
            {
                'exchange': 'opsconductor.system',
                'queue': 'audit-events.events',
                'routing_key': 'system.#'
            },
            
            # Dead Letter Bindings
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.auth-service',
                'routing_key': 'auth-service.failed'
            },
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.user-service',
                'routing_key': 'user-service.failed'
            },
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.universal-targets',
                'routing_key': 'universal-targets.failed'
            },
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.job-management',
                'routing_key': 'job-management.failed'
            },
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.job-execution',
                'routing_key': 'job-execution.failed'
            },
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.job-scheduling',
                'routing_key': 'job-scheduling.failed'
            },
            {
                'exchange': 'opsconductor.dlx',
                'queue': 'dlq.audit-events',
                'routing_key': 'audit-events.failed'
            }
        ]
        
        for binding in bindings:
            self.channel.queue_bind(
                exchange=binding['exchange'],
                queue=binding['queue'],
                routing_key=binding['routing_key']
            )
            logger.info(f"Bound queue {binding['queue']} to exchange {binding['exchange']} with routing key {binding['routing_key']}")
    
    def setup_policies(self):
        """Set up RabbitMQ policies for high availability and performance"""
        # Note: Policies are typically set via management API or rabbitmqctl
        # This is a placeholder for policy setup
        logger.info("RabbitMQ policies should be configured via management interface:")
        logger.info("1. High Availability: Set ha-mode=all for critical queues")
        logger.info("2. Message TTL: Set message-ttl for temporary queues")
        logger.info("3. Queue Length Limits: Set max-length for bounded queues")
    
    def run_setup(self):
        """Run complete RabbitMQ setup"""
        logger.info("Starting RabbitMQ setup for OpsConductor microservices...")
        
        self.connect()
        
        logger.info("Setting up exchanges...")
        self.setup_exchanges()
        
        logger.info("Setting up queues...")
        self.setup_queues()
        
        logger.info("Setting up bindings...")
        self.setup_bindings()
        
        logger.info("Policy recommendations...")
        self.setup_policies()
        
        logger.info("RabbitMQ setup completed successfully!")
        
        if self.connection and not self.connection.is_closed:
            self.connection.close()


if __name__ == "__main__":
    import os
    
    # Get RabbitMQ URL from environment or use default
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    setup = RabbitMQSetup(rabbitmq_url)
    setup.run_setup()