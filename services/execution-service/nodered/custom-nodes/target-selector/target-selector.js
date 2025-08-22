/**
 * OpsConductor Target Selector Node
 * Selects and filters OpsConductor targets for workflow execution
 */

module.exports = function(RED) {
    "use strict";
    
    function OpsConductorTargetSelector(config) {
        RED.nodes.createNode(this, config);
        const node = this;
        
        // Node configuration
        node.name = config.name || "OpsConductor Target Selector";
        node.targetFilter = config.targetFilter || {};
        node.outputFormat = config.outputFormat || 'array';
        
        // OpsConductor API configuration
        node.apiUrl = process.env.OPSCONDUCTOR_API_URL || 'http://targets-service:8000';
        node.apiToken = process.env.OPSCONDUCTOR_TOKEN;
        
        node.on('input', async function(msg, send, done) {
            try {
                node.status({fill: "blue", shape: "dot", text: "fetching targets..."});
                
                const axios = require('axios');
                
                // Build query parameters
                let queryParams = {};
                
                // Apply filters from configuration
                if (config.targetFilter.osType) {
                    queryParams.os_type = config.targetFilter.osType;
                }
                if (config.targetFilter.environment) {
                    queryParams.environment = config.targetFilter.environment;
                }
                if (config.targetFilter.status) {
                    queryParams.status = config.targetFilter.status;
                }
                
                // Apply dynamic filters from input message
                if (msg.targetFilter) {
                    Object.assign(queryParams, msg.targetFilter);
                }
                
                // Make API request to OpsConductor targets service
                const response = await axios.get(`${node.apiUrl}/api/targets`, {
                    params: queryParams,
                    headers: {
                        'Authorization': `Bearer ${node.apiToken}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000
                });
                
                if (response.status === 200 && response.data.status === 'success') {
                    let targets = response.data.targets || [];
                    
                    // Apply specific target selection if configured
                    if (config.selectedTargets && config.selectedTargets.length > 0) {
                        targets = targets.filter(target => 
                            config.selectedTargets.includes(target.id.toString())
                        );
                    }
                    
                    // Format output based on configuration
                    let output;
                    switch (config.outputFormat) {
                        case 'array':
                            output = targets;
                            break;
                        case 'ids':
                            output = targets.map(t => t.id);
                            break;
                        case 'names':
                            output = targets.map(t => t.name);
                            break;
                        case 'grouped':
                            output = targets.reduce((groups, target) => {
                                const env = target.environment || 'default';
                                if (!groups[env]) groups[env] = [];
                                groups[env].push(target);
                                return groups;
                            }, {});
                            break;
                        default:
                            output = targets;
                    }
                    
                    // Set output message
                    msg.targets = output;
                    msg.targetCount = targets.length;
                    msg.selectedAt = new Date().toISOString();
                    
                    node.status({
                        fill: "green", 
                        shape: "dot", 
                        text: `${targets.length} targets selected`
                    });
                    
                    send(msg);
                    done();
                    
                } else {
                    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
                }
                
            } catch (error) {
                node.error(`Target selection failed: ${error.message}`, msg);
                node.status({fill: "red", shape: "ring", text: "error"});
                done(error);
            }
        });
    }
    
    // Register the node
    RED.nodes.registerType("opsconductor-target-selector", OpsConductorTargetSelector);
};