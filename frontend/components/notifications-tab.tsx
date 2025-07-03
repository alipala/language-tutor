'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Bell, CheckCircle, Clock, AlertTriangle, Gift, Info, Wrench } from 'lucide-react';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();

interface Notification {
  id: string;
  title: string;
  content: string;
  notification_type: 'Maintenance' | 'Special Offer' | 'Information';
  created_at: string;
  is_read: boolean;
  read_at?: string;
}

interface NotificationListResponse {
  notifications: Array<{
    id: string;
    user_id: string;
    notification_id: string;
    is_read: boolean;
    read_at?: string;
    created_at: string;
    notification: Notification;
  }>;
  unread_count: number;
  total_count: number;
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'Maintenance':
      return <Wrench className="h-5 w-5 text-orange-500" />;
    case 'Special Offer':
      return <Gift className="h-5 w-5 text-green-500" />;
    case 'Information':
      return <Info className="h-5 w-5 text-blue-500" />;
    default:
      return <Bell className="h-5 w-5 text-gray-500" />;
  }
};

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'Maintenance':
      return 'bg-orange-50 border-orange-200';
    case 'Special Offer':
      return 'bg-green-50 border-green-200';
    case 'Information':
      return 'bg-blue-50 border-blue-200';
    default:
      return 'bg-gray-50 border-gray-200';
  }
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'Maintenance':
      return 'bg-orange-100 text-orange-700';
    case 'Special Offer':
      return 'bg-green-100 text-green-700';
    case 'Information':
      return 'bg-blue-100 text-blue-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
};

export default function NotificationsTab() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<NotificationListResponse['notifications']>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [markingRead, setMarkingRead] = useState<string | null>(null);

  const fetchNotifications = async () => {
    if (!user) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/notifications/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data: NotificationListResponse = await response.json();
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
        setTotalCount(data.total_count);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch notifications' }));
        throw new Error(errorData.detail || 'Failed to fetch notifications');
      }
    } catch (err: any) {
      console.error('Error fetching notifications:', err);
      setError(err.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    if (!user) return;

    setMarkingRead(notificationId);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/notifications/mark-read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notification_id: notificationId
        }),
      });

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(notif => 
            notif.notification_id === notificationId 
              ? { ...notif, is_read: true, read_at: new Date().toISOString() }
              : notif
          )
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to mark as read' }));
        console.error('Failed to mark notification as read:', errorData.detail);
      }
    } catch (err: any) {
      console.error('Error marking notification as read:', err);
    } finally {
      setMarkingRead(null);
    }
  };

  const markAllAsRead = async () => {
    if (!user || unreadCount === 0) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/notifications/mark-all-read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(notif => ({ 
            ...notif, 
            is_read: true, 
            read_at: new Date().toISOString() 
          }))
        );
        setUnreadCount(0);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to mark all as read' }));
        console.error('Failed to mark all notifications as read:', errorData.detail);
      }
    } catch (err: any) {
      console.error('Error marking all notifications as read:', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [user]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin h-8 w-8 border-2 border-teal-500 border-t-transparent rounded-full"></div>
          <span className="ml-3 text-gray-600">Loading notifications...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notifications Header */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Bell className="h-6 w-6 text-teal-500" />
            <h3 className="text-xl font-bold text-gray-800">Notifications</h3>
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">
                {unreadCount} unread
              </Badge>
            )}
          </div>
          
          {unreadCount > 0 && (
            <Button
              onClick={markAllAsRead}
              variant="outline"
              size="sm"
              className="text-teal-600 border-teal-200 hover:bg-teal-50"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Mark all as read
            </Button>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-teal-600">{totalCount}</div>
            <div className="text-sm text-teal-700">Total Notifications</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{unreadCount}</div>
            <div className="text-sm text-red-700">Unread</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{totalCount - unreadCount}</div>
            <div className="text-sm text-green-700">Read</div>
          </div>
        </div>
      </div>

      {/* Notifications List */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        {notifications.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <Bell className="h-8 w-8 text-gray-400" />
            </div>
            <h4 className="text-lg font-medium text-gray-800 mb-2">No Notifications</h4>
            <p className="text-gray-600">You don't have any notifications yet.</p>
          </div>
        ) : (
          <ScrollArea className="h-96">
            <div className="space-y-4">
              {notifications.map((userNotification) => {
                const notification = userNotification.notification;
                return (
                  <div
                    key={userNotification.id}
                    className={`border rounded-xl p-4 transition-all ${
                      userNotification.is_read 
                        ? 'bg-gray-50 border-gray-200 opacity-75' 
                        : getNotificationColor(notification.notification_type)
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        {getNotificationIcon(notification.notification_type)}
                        <div>
                          <h4 className="font-semibold text-gray-800 flex items-center">
                            {notification.title}
                            {!userNotification.is_read && (
                              <div className="w-2 h-2 bg-red-500 rounded-full ml-2"></div>
                            )}
                          </h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge 
                              variant="secondary" 
                              className={`text-xs ${getTypeColor(notification.notification_type)}`}
                            >
                              {notification.notification_type}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {new Date(notification.created_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {!userNotification.is_read && (
                        <Button
                          onClick={() => markAsRead(userNotification.notification_id)}
                          disabled={markingRead === userNotification.notification_id}
                          variant="outline"
                          size="sm"
                          className="text-teal-600 border-teal-200 hover:bg-teal-50"
                        >
                          {markingRead === userNotification.notification_id ? (
                            <div className="animate-spin h-3 w-3 border border-teal-600 border-t-transparent rounded-full"></div>
                          ) : (
                            <CheckCircle className="h-3 w-3" />
                          )}
                        </Button>
                      )}
                    </div>
                    
                    <div 
                      className="text-sm text-gray-700 prose prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: notification.content }}
                    />
                    
                    {userNotification.is_read && userNotification.read_at && (
                      <div className="flex items-center text-xs text-gray-500 mt-3">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Read on {new Date(userNotification.read_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </div>
    </div>
  );
}
