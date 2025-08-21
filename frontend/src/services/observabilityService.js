/**
 * Observability Service
 * Handles communication with Prometheus, Grafana, and Loki APIs
 */

class ObservabilityService {
  constructor() {
    this.prometheusUrl = process.env.REACT_APP_PROMETHEUS_URL || 'http://localhost:9090';
    this.grafanaUrl = process.env.REACT_APP_GRAFANA_URL || 'http://localhost:3001';
    this.lokiUrl = process.env.REACT_APP_LOKI_URL || 'http://localhost:3100';
  }

  /**
   * Fetch Prometheus targets
   */
  async getPrometheusTargets() {
    try {
      const response = await fetch(`${this.prometheusUrl}/api/v1/targets`);
      const data = await response.json();
      return data.data?.activeTargets || [];
    } catch (error) {
      console.error('Error fetching Prometheus targets:', error);
      throw error;
    }
  }

  /**
   * Query Prometheus metrics
   */
  async queryPrometheus(query) {
    try {
      const response = await fetch(
        `${this.prometheusUrl}/api/v1/query?query=${encodeURIComponent(query)}`
      );
      const data = await response.json();
      return data.status === 'success' ? data.data.result : [];
    } catch (error) {
      console.error(`Error querying Prometheus with query "${query}":`, error);
      throw error;
    }
  }

  /**
   * Query Prometheus metrics over time range
   */
  async queryPrometheusRange(query, start, end, step = '15s') {
    try {
      const params = new URLSearchParams({
        query,
        start: start.toISOString(),
        end: end.toISOString(),
        step
      });
      
      const response = await fetch(
        `${this.prometheusUrl}/api/v1/query_range?${params}`
      );
      const data = await response.json();
      return data.status === 'success' ? data.data.result : [];
    } catch (error) {
      console.error(`Error querying Prometheus range with query "${query}":`, error);
      throw error;
    }
  }

  /**
   * Get service health status
   */
  async getServiceHealth() {
    try {
      const upMetrics = await this.queryPrometheus('up');
      const services = {};
      
      upMetrics.forEach(metric => {
        const serviceName = metric.metric.job || metric.metric.service;
        const isUp = metric.value[1] === '1';
        services[serviceName] = {
          name: serviceName,
          status: isUp ? 'healthy' : 'unhealthy',
          component: metric.metric.component || 'unknown',
          instance: metric.metric.instance,
          lastScrape: new Date().toISOString()
        };
      });
      
      return services;
    } catch (error) {
      console.error('Error fetching service health:', error);
      throw error;
    }
  }

  /**
   * Get HTTP request metrics
   */
  async getHttpRequestMetrics() {
    try {
      const metrics = await this.queryPrometheus('http_requests_total');
      const requestData = {};
      
      metrics.forEach(metric => {
        const service = metric.metric.service || metric.metric.job;
        if (!requestData[service]) {
          requestData[service] = {
            total: 0,
            byStatus: {},
            byHandler: {}
          };
        }
        
        const count = parseInt(metric.value[1]);
        requestData[service].total += count;
        
        const status = metric.metric.status || 'unknown';
        requestData[service].byStatus[status] = (requestData[service].byStatus[status] || 0) + count;
        
        const handler = metric.metric.handler || 'unknown';
        requestData[service].byHandler[handler] = (requestData[service].byHandler[handler] || 0) + count;
      });
      
      return requestData;
    } catch (error) {
      console.error('Error fetching HTTP request metrics:', error);
      throw error;
    }
  }

  /**
   * Get nginx-specific metrics
   */
  async getNginxMetrics() {
    try {
      const [connections, requests] = await Promise.all([
        this.queryPrometheus('nginx_connections_active'),
        this.queryPrometheus('nginx_http_requests_total')
      ]);
      
      return {
        activeConnections: connections[0]?.value[1] || '0',
        totalRequests: requests[0]?.value[1] || '0'
      };
    } catch (error) {
      console.error('Error fetching nginx metrics:', error);
      throw error;
    }
  }

  /**
   * Get memory usage metrics
   */
  async getMemoryMetrics() {
    try {
      const metrics = await this.queryPrometheus('process_resident_memory_bytes');
      const memoryData = {};
      
      metrics.forEach(metric => {
        const service = metric.metric.service || metric.metric.job;
        const bytes = parseInt(metric.value[1]);
        memoryData[service] = {
          bytes,
          formatted: this.formatBytes(bytes)
        };
      });
      
      return memoryData;
    } catch (error) {
      console.error('Error fetching memory metrics:', error);
      throw error;
    }
  }

  /**
   * Query Loki logs
   */
  async queryLoki(query, start, end, limit = 100) {
    try {
      const params = new URLSearchParams({
        query,
        start: (start.getTime() * 1000000).toString(), // Convert to nanoseconds
        end: (end.getTime() * 1000000).toString(),
        limit: limit.toString()
      });
      
      const response = await fetch(
        `${this.lokiUrl}/loki/api/v1/query_range?${params}`
      );
      const data = await response.json();
      return data.data?.result || [];
    } catch (error) {
      console.error(`Error querying Loki with query "${query}":`, error);
      throw error;
    }
  }

  /**
   * Get available log labels
   */
  async getLogLabels() {
    try {
      const response = await fetch(`${this.lokiUrl}/loki/api/v1/labels`);
      const data = await response.json();
      return data.data || [];
    } catch (error) {
      console.error('Error fetching log labels:', error);
      throw error;
    }
  }

  /**
   * Get log label values
   */
  async getLogLabelValues(label) {
    try {
      const response = await fetch(`${this.lokiUrl}/loki/api/v1/label/${label}/values`);
      const data = await response.json();
      return data.data || [];
    } catch (error) {
      console.error(`Error fetching values for label "${label}":`, error);
      throw error;
    }
  }

  /**
   * Get comprehensive observability overview
   */
  async getObservabilityOverview() {
    try {
      const [
        targets,
        serviceHealth,
        httpMetrics,
        nginxMetrics,
        memoryMetrics
      ] = await Promise.all([
        this.getPrometheusTargets(),
        this.getServiceHealth(),
        this.getHttpRequestMetrics(),
        this.getNginxMetrics(),
        this.getMemoryMetrics()
      ]);

      return {
        targets,
        services: serviceHealth,
        httpRequests: httpMetrics,
        nginx: nginxMetrics,
        memory: memoryMetrics,
        summary: {
          totalServices: Object.keys(serviceHealth).length,
          healthyServices: Object.values(serviceHealth).filter(s => s.status === 'healthy').length,
          totalTargets: targets.length,
          healthyTargets: targets.filter(t => t.health === 'up').length
        }
      };
    } catch (error) {
      console.error('Error fetching observability overview:', error);
      throw error;
    }
  }

  /**
   * Utility function to format bytes
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get Grafana dashboard URLs
   */
  getGrafanaUrls() {
    return {
      main: this.grafanaUrl,
      explore: `${this.grafanaUrl}/explore`,
      dashboards: `${this.grafanaUrl}/dashboards`
    };
  }

  /**
   * Get Prometheus URLs
   */
  getPrometheusUrls() {
    return {
      main: this.prometheusUrl,
      targets: `${this.prometheusUrl}/targets`,
      graph: `${this.prometheusUrl}/graph`
    };
  }
}

export default new ObservabilityService();