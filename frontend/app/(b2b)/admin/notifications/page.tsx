'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

interface Notification {
  id: string;
  title: string;
  content: string;
  notification_type: string;
  target_user_ids: string[] | null;
  send_immediately: boolean;
  scheduled_send_time: string | null;
  is_sent: boolean;
  sent_at: string | null;
  created_at: string;
  created_by: string;
}

const NotificationTypes = [
  { value: 'Maintenance', label: '🔧 Maintenance', color: 'bg-orange-100 text-orange-800', bgColor: 'bg-orange-50', borderColor: 'border-orange-200' },
  { value: 'Special Offer', label: '🎉 Special Offer', color: 'bg-green-100 text-green-800', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
  { value: 'Information', label: '📢 Information', color: 'bg-blue-100 text-blue-800', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' }
];

export default function AdminNotificationsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    notification_type: 'Information',
    target_user_ids: [] as string[],
    send_immediately: true,
    scheduled_send_time: ''
  });

  // API base URL
  const isRailway = typeof window !== 'undefined' && (
    window.location.hostname.includes('railway.app') || 
    window.location.hostname === 'mytacoai.com'
  );
  const API_URL = isRailway ? '' : 'http://localhost:8000';

  // Check if user is admin
  useEffect(() => {
    if (!user || !user.email?.includes('admin')) {
      router.push('/');
      return;
    }
  }, [user, router]);

  // Fetch notifications and users
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token || !user) return;
    
    const fetchData = async () => {
      try {
        const [notificationsRes, usersRes] = await Promise.all([
          fetch(`${API_URL}/api/admin/notifications?page=1&per_page=50&sort_field=created_at&sort_order=desc`, {
            headers: { 'Authorization': `Bearer ${token}` }
          }),
          fetch(`${API_URL}/api/admin/notifications/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
        ]);

        if (notificationsRes.ok) {
          const notificationsData = await notificationsRes.json();
          setNotifications(notificationsData);
        }

        if (usersRes.ok) {
          const usersData = await usersRes.json();
          setUsers(usersData);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, API_URL]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setShowConfirmModal(true);
  };

  const confirmSend = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          target_user_ids: formData.target_user_ids.length > 0 ? formData.target_user_ids : null
        })
      });

      if (response.ok) {
        alert('🎉 Notification created successfully!');
        setShowCreateForm(false);
        setShowConfirmModal(false);
        setFormData({
          title: '',
          content: '',
          notification_type: 'Information',
          target_user_ids: [],
          send_immediately: true,
          scheduled_send_time: ''
        });
        // Refresh notifications
        window.location.reload();
      } else {
        alert('❌ Error creating notification');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('❌ Error creating notification');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTypeConfig = (type: string) => {
    return NotificationTypes.find(t => t.value === type) || NotificationTypes[2];
  };

  if (!user || !user.email?.includes('admin')) {
    return <div>Access denied</div>;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5-5-5h5v-5a7.5 7.5 0 00-15 0v5h5l-5 5-5-5h5V7a12 12 0 0124 0v10z" />
              </svg>
            </div>
          </div>
          <p className="mt-4 text-lg font-medium text-gray-700">Loading your notification center...</p>
          <p className="text-sm text-gray-500">Preparing the professional interface</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Modern Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <div className="p-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Notification Center
              </h1>
              <p className="text-lg text-gray-600 mt-1">
                Manage and send notifications to your users
              </p>
            </div>
          </div>
          
          <div className="h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-green-500 rounded-full mb-4"></div>
          
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.back()}
                className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span>Back to Dashboard</span>
              </button>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Create Notification</span>
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100">
          <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-blue-50 rounded-t-2xl">
            <h2 className="text-xl font-bold text-gray-900">Recent Notifications</h2>
            <p className="text-gray-600 mt-1">Manage and track your notification campaigns</p>
          </div>
          <div className="divide-y divide-gray-100">
            {notifications.length === 0 ? (
              <div className="px-8 py-16 text-center">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No notifications yet</h3>
                <p className="text-gray-500 mb-4">Create your first notification to engage with your users</p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Create Your First Notification
                </button>
              </div>
            ) : (
              notifications.map((notification) => {
                const typeConfig = getTypeConfig(notification.notification_type);
                return (
                  <div key={notification.id} className="px-8 py-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-4 mb-3">
                          <div className={`p-2 rounded-lg ${typeConfig.bgColor}`}>
                            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                            </svg>
                          </div>
                          <h3 className="text-xl font-bold text-gray-900">{notification.title}</h3>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${typeConfig.color}`}>
                            {typeConfig.label}
                          </span>
                          {notification.is_sent ? (
                            <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                              ✅ Sent
                            </span>
                          ) : (
                            <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                              ⏳ Pending
                            </span>
                          )}
                        </div>
                        <div className="text-gray-600 mb-3" dangerouslySetInnerHTML={{ 
                          __html: notification.content.substring(0, 200) + (notification.content.length > 200 ? '...' : '') 
                        }} />
                        <div className="flex items-center gap-6 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Created: {formatDate(notification.created_at)}
                          </span>
                          {notification.sent_at && (
                            <span className="flex items-center gap-1">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              Sent: {formatDate(notification.sent_at)}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.196-2.121M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.196-2.121M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            {notification.target_user_ids ? `${notification.target_user_ids.length} users` : 'All users'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Create Form Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-2xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Create Push Notification</h2>
                      <p className="text-gray-600">Send notifications to your users with customizable content and scheduling</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowCreateForm(false)}
                    className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="p-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left Column */}
                  <div className="space-y-6">
                    {/* Title Section */}
                    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 transition-all duration-300 hover:border-gray-300 hover:shadow-lg hover:-translate-y-1">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-3 bg-blue-100 rounded-lg">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a1.994 1.994 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Notification Title</h3>
                          <p className="text-sm text-gray-600">Create an engaging title for your notification</p>
                        </div>
                      </div>
                      <input
                        type="text"
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        placeholder="Enter notification title"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-medium"
                        required
                      />
                    </div>

                    {/* Type Section */}
                    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 transition-all duration-300 hover:border-gray-300 hover:shadow-lg hover:-translate-y-1">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-3 bg-purple-100 rounded-lg">
                          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a1.994 1.994 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Notification Type</h3>
                          <p className="text-sm text-gray-600">Choose the type of notification</p>
                        </div>
                      </div>
                      <select
                        value={formData.notification_type}
                        onChange={(e) => setFormData({ ...formData, notification_type: e.target.value })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-medium"
                        required
                      >
                        {NotificationTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Recipients Section */}
                    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 transition-all duration-300 hover:border-gray-300 hover:shadow-lg hover:-translate-y-1">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-3 bg-green-100 rounded-lg">
                          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.196-2.121M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.196-2.121M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Recipients</h3>
                          <p className="text-sm text-gray-600">Choose who will receive this notification</p>
                        </div>
                      </div>
                      <select
                        value={formData.target_user_ids.length > 0 ? 'specific' : 'all'}
                        onChange={(e) => {
                          if (e.target.value === 'all') {
                            setFormData({ ...formData, target_user_ids: [] });
                          }
                        }}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 font-medium"
                      >
                        <option value="all">📢 Send to All Users</option>
                        <option value="specific">👥 Select Specific Users</option>
                      </select>
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-6">
                    {/* Message Content */}
                    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 transition-all duration-300 hover:border-gray-300 hover:shadow-lg hover:-translate-y-1">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-3 bg-indigo-100 rounded-lg">
                          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Message Content</h3>
                          <p className="text-sm text-gray-600">Write your notification message</p>
                        </div>
                      </div>
                      <textarea
                        value={formData.content}
                        onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                        placeholder="Write your notification message here..."
                        rows={6}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                        required
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        💡 You can use basic HTML tags like &lt;b&gt;, &lt;i&gt;, &lt;br&gt; for formatting
                      </p>
                    </div>

                    {/* Delivery Schedule */}
                    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 transition-all duration-300 hover:border-gray-300 hover:shadow-lg hover:-translate-y-1">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-3 bg-orange-100 rounded-lg">
                          <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Delivery Schedule</h3>
                          <p className="text-sm text-gray-600">Choose when to send your notification</p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <label className="flex items-center space-x-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.send_immediately}
                            onChange={(e) => setFormData({ ...formData, send_immediately: e.target.checked })}
                            className="w-5 h-5 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                          />
                          <div className="flex items-center space-x-2">
                            <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span className="font-medium text-gray-900">Send Immediately</span>
                          </div>
                        </label>

                        {!formData.send_immediately && (
                          <div className="transition-all duration-300 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="flex items-center space-x-2 mb-3">
                              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <span className="font-medium text-blue-800">Schedule for Later</span>
                            </div>
                            <input
                              type="datetime-local"
                              value={formData.scheduled_send_time}
                              onChange={(e) => setFormData({ ...formData, scheduled_send_time: e.target.value })}
                              className="w-full px-4 py-3 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                              required={!formData.send_immediately}
                            />
                            <p className="text-sm text-gray-600 mt-2">
                              Notification will be automatically sent at the specified time
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="mt-8 flex justify-end space-x-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    <span>Create Notification</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Confirmation Modal */}
        {showConfirmModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl">
              <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-2xl">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-500 rounded-lg">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Confirm Notification</h3>
                    <p className="text-sm text-gray-600">Review your notification before sending</p>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900">Title:</h4>
                    <p className="text-gray-600">{formData.title}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Type:</h4>
                    <p className="text-gray-600">{formData.notification_type}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Recipients:</h4>
                    <p className="text-gray-600">
                      {formData.target_user_ids.length > 0 ? `${formData.target_user_ids.length} specific users` : 'All users'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Schedule:</h4>
                    <p className="text-gray-600">
                      {formData.send_immediately ? 'Send immediately' : `Scheduled for ${formData.scheduled_send_time}`}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Message:</h4>
                    <div className="text-gray-600 p-3 bg-gray-50 rounded-lg" dangerouslySetInnerHTML={{ __html: formData.content }} />
                  </div>
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50 rounded-b-2xl">
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowConfirmModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmSend}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                  >
                    Send Notification
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
