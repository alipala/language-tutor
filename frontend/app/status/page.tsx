'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, XCircle, Clock, Activity, Server, Database, Zap } from 'lucide-react';

const SystemStatus: React.FC = () => {
  const services = [
    {
      name: "API Gateway",
      status: "operational",
      uptime: "99.9%",
      responseTime: "45ms",
      icon: Server
    },
    {
      name: "AI Conversation Engine",
      status: "operational", 
      uptime: "99.8%",
      responseTime: "120ms",
      icon: Zap
    },
    {
      name: "Speech Recognition",
      status: "operational",
      uptime: "99.7%",
      responseTime: "200ms",
      icon: Activity
    },
    {
      name: "Database",
      status: "operational",
      uptime: "99.9%",
      responseTime: "15ms",
      icon: Database
    },
    {
      name: "Authentication Service",
      status: "operational",
      uptime: "99.9%",
      responseTime: "30ms",
      icon: CheckCircle
    },
    {
      name: "File Storage",
      status: "degraded",
      uptime: "98.5%",
      responseTime: "350ms",
      icon: Server
    }
  ];

  const incidents = [
    {
      date: "January 12, 2025",
      title: "Temporary slowdown in speech recognition",
      status: "resolved",
      duration: "45 minutes",
      description: "Users experienced slower response times during speech assessment. Issue was resolved by scaling up processing capacity."
    },
    {
      date: "January 8, 2025", 
      title: "Brief API gateway timeout",
      status: "resolved",
      duration: "12 minutes",
      description: "Some users experienced connection timeouts. Issue was quickly resolved with a service restart."
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'down':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'down':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold mb-6">System Status</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Real-time status and performance metrics for all Language Tutor services.
            </p>
            <div className="mt-8 inline-flex items-center bg-white/20 rounded-full px-6 py-3">
              <CheckCircle className="w-6 h-6 text-green-300 mr-3" />
              <span className="text-lg font-medium">All Systems Operational</span>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-8 text-center">Service Status</h2>
            <div className="space-y-4">
              {services.map((service, index) => (
                <motion.div
                  key={service.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                  className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mr-4">
                        <service.icon className="w-6 h-6 text-[#4ECFBF]" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-gray-800">{service.name}</h3>
                        <div className="flex items-center mt-1">
                          {getStatusIcon(service.status)}
                          <span className={`ml-2 px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(service.status)}`}>
                            {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500 mb-1">Uptime</div>
                      <div className="text-lg font-bold text-gray-800">{service.uptime}</div>
                      <div className="text-sm text-gray-500 mt-2">Response Time</div>
                      <div className="text-lg font-bold text-gray-800">{service.responseTime}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-8 text-center">Recent Incidents</h2>
            <div className="space-y-6">
              {incidents.map((incident, index) => (
                <div key={index} className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-800 mb-2">{incident.title}</h3>
                      <div className="flex items-center text-gray-500 text-sm">
                        <Clock className="w-4 h-4 mr-2" />
                        <span className="mr-4">{incident.date}</span>
                        <span className="mr-4">Duration: {incident.duration}</span>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          {incident.status.charAt(0).toUpperCase() + incident.status.slice(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="text-gray-600 leading-relaxed">{incident.description}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Subscribe to Updates</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Get notified about service updates, maintenance windows, and incident reports.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent"
              />
              <button className="px-6 py-3 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300">
                Subscribe
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
