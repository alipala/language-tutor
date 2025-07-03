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
  { value: 'Maintenance', label: 'Maintenance', color: 'bg-orange-100 text-orange-800' },
  { value: 'Special Offer', label: 'Special Offer', color: 'bg-green-100 text-green-800' },
  { value: 'Information', label: 'Information', color: 'bg-blue-100 text-blue-800' }
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
        alert('Notification created successfully!');
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
        alert('Error creating notification');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error creating notification');
    }
  };

  const toggleUserSelection = (userId: string) => {
    setFormData(prev => ({
      ...prev,
      target_user_ids: prev.target_user_ids.includes(userId)
        ? prev.target_user_ids.filter(id => id !== userId)
        : [...prev.target_user_ids, userId]
    }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!user || !user.email?.includes('admin')) {
    return <div>Access denied</div>;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Notification Center</h1>
              <p className="mt-2 text-gray-600">Manage and send notifications to users</p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Create Notification
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Notifications</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {notifications.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <div className="text-gray-400 text-lg mb-2">📢</div>
                <p className="text-gray-500">No notifications yet</p>
                <p className="text-sm text-gray-400 mt-1">Create your first notification to get started</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div key={notification.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{notification.title}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          NotificationTypes.find(t => t.value === notification.notification_type)?.color || 'bg-gray-100 text-gray-800'
                        }`}>
                          {notification.notification_type}
                        </span>
                        {notification.is_sent ? (
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Sent
                          </span>
                        ) : (
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Pending
                          </span>
                        )}
                      </div>
                      <div className="text-gray-600 mb-2" dangerouslySetInnerHTML={{ __html: notification.content.substring(0, 200) + (notification.content.length > 200 ? '...' : '') }} />
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>Created: {formatDate(notification.created_at)}</span>
                        {notification.sent_at && <span>Sent: {formatDate(notification.sent_at)}</span>}
                        <span>
                          Target: {notification.target_user_ids ? `${notification.target_user_ids.length} users` : 'All users'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Create Notification Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Create New Notification</h2>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {/* Title and Type */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Title *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.title}
                      onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter notification title"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Type *
                    </label>
                    <select
                      value={formData.notification_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, notification_type: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {NotificationTypes.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content *
                  </label>
                  <textarea
                    required
                    rows={6}
                    value={formData.content}
                    onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter notification content... (HTML tags supported: <b>, <i>, <u>, <br>, <p>)"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    💡 You can use basic HTML tags: &lt;b&gt;bold&lt;/b&gt;, &lt;i&gt;italic&lt;/i&gt;, &lt;u&gt;underline&lt;/u&gt;, &lt;br&gt; for line breaks
                  </p>
                </div>

                {/* Target Users */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Users
                  </label>
                  <div className="border border-gray-300 rounded-md p-4 max-h-48 overflow-y-auto">
                    <div className="mb-3">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.target_user_ids.length === 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData(prev => ({ ...prev, target_user_ids: [] }));
                            }
                          }}
                          className="mr-2"
                        />
                        <span className="font-medium text-blue-600">Send to All Users</span>
                      </label>
                    </div>
                    <div className="space-y-2">
                      {users.map(user => (
                        <label key={user.id} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.target_user_ids.includes(user.id)}
                            onChange={() => toggleUserSelection(user.id)}
                            className="mr-2"
                          />
                          <span className="text-sm">
                            {user.name} ({user.email})
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                  {formData.target_user_ids.length > 0 && (
                    <p className="mt-2 text-sm text-gray-600">
                      {formData.target_user_ids.length} user(s) selected
                    </p>
                  )}
                </div>

                {/* Scheduling */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Scheduling
                  </label>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="scheduling"
                        checked={formData.send_immediately}
                        onChange={() => setFormData(prev => ({ ...prev, send_immediately: true }))}
                        className="mr-2"
                      />
                      <span>Send Immediately</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="scheduling"
                        checked={!formData.send_immediately}
                        onChange={() => setFormData(prev => ({ ...prev, send_immediately: false }))}
                        className="mr-2"
                      />
                      <span>Schedule for Later</span>
                    </label>
                    {!formData.send_immediately && (
                      <div className="ml-6">
                        <input
                          type="datetime-local"
                          value={formData.scheduled_send_time}
                          onChange={(e) => setFormData(prev => ({ ...prev, scheduled_send_time: e.target.value }))}
                          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required={!formData.send_immediately}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                  >
                    Create Notification
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Confirmation Modal */}
        {showConfirmModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Confirm Notification</h2>
              </div>
              <div className="p-6">
                <div className="mb-4">
                  <h3 className="font-medium text-gray-900 mb-2">{formData.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">Type: {formData.notification_type}</p>
                  <p className="text-sm text-gray-600 mb-2">
                    Target: {formData.target_user_ids.length === 0 ? 'All users' : `${formData.target_user_ids.length} selected users`}
                  </p>
                  <p className="text-sm text-gray-600">
                    Schedule: {formData.send_immediately ? 'Send immediately' : `Send on ${formData.scheduled_send_time}`}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded-md mb-4">
                  <div className="text-sm" dangerouslySetInnerHTML={{ __html: formData.content }} />
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Are you sure you want to send this notification?
                </p>
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setShowConfirmModal(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmSend}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
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
