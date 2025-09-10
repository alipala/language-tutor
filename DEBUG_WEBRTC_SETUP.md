# 🐛 Debug Setup: Universal WebRTC Compatibility
## VSCode Debugging Instructions for Innovation #1

---

## 🚀 **Quick Start Debug Setup**

### **1. Current Server Status** ✅
```bash
# Frontend (Terminal 1)
cd frontend
npm run dev
# Running on: http://localhost:3000

# Backend (Terminal 2) 
cd backend
python run_with_venv.py
# Running on: http://localhost:8000
```

### **2. VSCode Debug Configuration**

Create `.vscode/launch.json` in your project root:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Frontend (Chrome)",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/frontend",
      "sourceMaps": true,
      "userDataDir": "${workspaceFolder}/.vscode/chrome-debug-profile",
      "runtimeArgs": [
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--allow-running-insecure-content"
      ]
    },
    {
      "name": "Debug Mobile Simulation",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/frontend",
      "runtimeArgs": [
        "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
      ]
    }
  ]
}
```

---

## 🔍 **Debug the isMobileBrowser() Function**

### **Step 1: Add Debug Breakpoints**

Open `frontend/lib/enhancedRealtimeService.ts` and add debugging:

```typescript
/**
 * PROBLEM: Mobile browsers behave differently than desktop
 * SOLUTION: Detect mobile and apply device-specific optimizations
 */
private isMobileBrowser(): boolean {
  const userAgent = window.navigator.userAgent.toLowerCase();
  console.log('🔍 [DEBUG] User Agent:', userAgent);
  
  const mobileKeywords = [
    'iphone', 'ipad', 'ipod', 'android', 'mobile', 'phone', 
    'tablet', 'touch', 'webos', 'blackberry'
  ];
  
  const isMobile = mobileKeywords.some(keyword => {
    const found = userAgent.includes(keyword);
    if (found) {
      console.log('🔍 [DEBUG] Mobile keyword found:', keyword);
    }
    return found;
  });
  
  console.log('🔍 [DEBUG] Is Mobile Browser:', isMobile);
  console.log('🔍 [DEBUG] Detected Keywords:', mobileKeywords.filter(k => userAgent.includes(k)));
  
  return isMobile;
}
```

### **Step 2: Add Enhanced Debugging**

Create a comprehensive debug function:

```typescript
/**
 * Enhanced debugging for WebRTC compatibility
 */
private debugBrowserCapabilities(): void {
  console.group('🔍 [DEBUG] Browser Capabilities Analysis');
  
  // Basic browser detection
  const userAgent = navigator.userAgent;
  console.log('User Agent:', userAgent);
  console.log('Platform:', navigator.platform);
  console.log('Language:', navigator.language);
  
  // Mobile detection breakdown
  const isMobile = this.isMobileBrowser();
  console.log('Is Mobile:', isMobile);
  
  // Browser type detection
  const isChrome = userAgent.includes('Chrome');
  const isSafari = userAgent.includes('Safari') && !isChrome;
  const isFirefox = userAgent.includes('Firefox');
  const isEdge = userAgent.includes('Edge');
  
  console.log('Browser Detection:', {
    chrome: isChrome,
    safari: isSafari,
    firefox: isFirefox,
    edge: isEdge
  });
  
  // WebRTC support detection
  const hasGetUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  const hasRTCPeerConnection = !!(window.RTCPeerConnection);
  
  console.log('WebRTC Support:', {
    getUserMedia: hasGetUserMedia,
    RTCPeerConnection: hasRTCPeerConnection
  });
  
  // Screen dimensions
  console.log('Screen Info:', {
    width: window.screen.width,
    height: window.screen.height,
    devicePixelRatio: window.devicePixelRatio
  });
  
  console.groupEnd();
}
```

### **Step 3: Test Different User Agents**

Add this test function to your component:

```typescript
/**
 * Test mobile detection with different user agents
 */
private testMobileDetection(): void {
  const testUserAgents = [
    // Desktop browsers
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    
    // Mobile browsers
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
  ];
  
  console.group('🧪 [TEST] Mobile Detection Tests');
  
  testUserAgents.forEach((ua, index) => {
    // Temporarily override userAgent for testing
    Object.defineProperty(navigator, 'userAgent', {
      value: ua,
      configurable: true
    });
    
    const isMobile = this.isMobileBrowser();
    const deviceType = ua.includes('iPhone') ? 'iPhone' : 
                      ua.includes('iPad') ? 'iPad' :
                      ua.includes('Android') ? 'Android' :
                      ua.includes('Chrome') ? 'Desktop Chrome' :
                      ua.includes('Firefox') ? 'Desktop Firefox' :
                      ua.includes('Safari') ? 'Desktop Safari' : 'Unknown';
    
    console.log(`Test ${index + 1} - ${deviceType}:`, isMobile);
  });
  
  console.groupEnd();
  
  // Restore original userAgent
  location.reload();
}
```

---

## 🛠️ **Debug WebRTC Constraints**

### **Step 4: Debug Universal Constraints**

Add this enhanced constraint debugging:

```typescript
/**
 * Debug universal constraints generation
 */
private debugUniversalConstraints(): MediaStreamConstraints {
  console.group('🔍 [DEBUG] Universal Constraints Generation');
  
  const isMobile = this.isMobileBrowser();
  const userAgent = navigator.userAgent.toLowerCase();
  
  // Browser detection
  const isChrome = userAgent.includes('chrome');
  const isSafari = userAgent.includes('safari') && !isChrome;
  const isFirefox = userAgent.includes('firefox');
  
  console.log('Browser Detection:', { isChrome, isSafari, isFirefox, isMobile });
  
  const constraints: MediaStreamConstraints = {
    audio: {
      // ✅ Standard WebRTC constraints (supported by all browsers)
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      
      // ✅ Chrome/Chromium-based browsers
      ...(isChrome && {
        googEchoCancellationType: "system",
        googNoiseSuppressionLevel: 2,
        googExperimentalEchoCancellation: true,
        googAutoGainControl2: true,
        googHighpassFilter: true,
        googTypingNoiseDetection: true,
        googAudioMirroring: false,
        googDAEchoCancellation: true,
        googNoiseSuppression2: true,
      }),
      
      // ✅ Firefox-specific optimizations
      ...(isFirefox && {
        mozEchoCancellation: true,
        mozNoiseSuppression: true,
        mozAutoGainControl: true,
      }),
      
      // ✅ Safari/WebKit optimizations
      ...(isSafari && {
        webkitEchoCancellation: true,
        webkitNoiseSuppression: true,
        webkitAutoGainControl: true,
      }),
      
      // ✅ Mobile optimizations
      ...(isMobile && {
        latency: { ideal: 0.01, max: 0.02 },
        sampleRate: { ideal: 48000 },
        channelCount: { ideal: 1, max: 1 },
        sampleSize: { ideal: 16 },
        volume: { ideal: 1.0 }
      })
    }
  };
  
  console.log('Generated Constraints:', JSON.stringify(constraints, null, 2));
  console.groupEnd();
  
  return constraints;
}
```

### **Step 5: Debug WebRTC Connection**

Add comprehensive connection debugging:

```typescript
/**
 * Debug WebRTC connection establishment
 */
private async debugWebRTCConnection(): Promise<void> {
  console.group('🔍 [DEBUG] WebRTC Connection Debug');
  
  try {
    // Step 1: Test getUserMedia
    console.log('Step 1: Testing getUserMedia...');
    const constraints = this.debugUniversalConstraints();
    
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    console.log('✅ getUserMedia successful:', stream);
    console.log('Audio tracks:', stream.getAudioTracks().length);
    
    // Step 2: Analyze audio tracks
    stream.getAudioTracks().forEach((track, index) => {
      console.log(`Audio Track ${index}:`, {
        id: track.id,
        kind: track.kind,
        label: track.label,
        enabled: track.enabled,
        muted: track.muted,
        readyState: track.readyState,
        settings: track.getSettings(),
        capabilities: track.getCapabilities()
      });
    });
    
    // Step 3: Test RTCPeerConnection
    console.log('Step 2: Testing RTCPeerConnection...');
    const peerConnection = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });
    
    console.log('✅ RTCPeerConnection created:', peerConnection);
    
    // Step 4: Add tracks to peer connection
    stream.getTracks().forEach(track => {
      peerConnection.addTrack(track, stream);
      console.log('✅ Track added to peer connection:', track.kind);
    });
    
    // Step 5: Test connection state changes
    peerConnection.onconnectionstatechange = () => {
      console.log('Connection state changed:', peerConnection.connectionState);
    };
    
    peerConnection.oniceconnectionstatechange = () => {
      console.log('ICE connection state changed:', peerConnection.iceConnectionState);
    };
    
    console.log('✅ WebRTC connection debug completed successfully');
    
  } catch (error) {
    console.error('❌ WebRTC connection debug failed:', error);
    
    // Detailed error analysis
    if (error.name === 'NotAllowedError') {
      console.error('User denied microphone permission');
    } else if (error.name === 'NotFoundError') {
      console.error('No microphone found');
    } else if (error.name === 'NotReadableError') {
      console.error('Microphone is being used by another application');
    } else if (error.name === 'OverconstrainedError') {
      console.error('Constraints cannot be satisfied:', error.constraint);
    }
  }
  
  console.groupEnd();
}
```

---

## 🧪 **Testing Instructions**

### **Step 6: Add Debug UI Component**

Create `frontend/components/debug/WebRTCDebugPanel.tsx`:

```tsx
'use client';

import React, { useState, useEffect } from 'react';

export const WebRTCDebugPanel: React.FC = () => {
  const [debugInfo, setDebugInfo] = useState<any>({});
  const [isDebugging, setIsDebugging] = useState(false);

  const runDebugTests = async () => {
    setIsDebugging(true);
    
    try {
      // Test mobile detection
      const userAgent = navigator.userAgent.toLowerCase();
      const mobileKeywords = ['iphone', 'ipad', 'ipod', 'android', 'mobile', 'phone', 'tablet', 'touch', 'webos', 'blackberry'];
      const isMobile = mobileKeywords.some(keyword => userAgent.includes(keyword));
      
      // Test WebRTC support
      const hasGetUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
      const hasRTCPeerConnection = !!(window.RTCPeerConnection);
      
      // Test constraints
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      };
      
      let streamInfo = null;
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamInfo = {
          success: true,
          audioTracks: stream.getAudioTracks().length,
          tracks: stream.getAudioTracks().map(track => ({
            id: track.id,
            label: track.label,
            enabled: track.enabled,
            settings: track.getSettings()
          }))
        };
        stream.getTracks().forEach(track => track.stop()); // Clean up
      } catch (error) {
        streamInfo = {
          success: false,
          error: error.message
        };
      }
      
      setDebugInfo({
        userAgent,
        isMobile,
        webrtcSupport: {
          getUserMedia: hasGetUserMedia,
          RTCPeerConnection: hasRTCPeerConnection
        },
        streamTest: streamInfo,
        browserInfo: {
          platform: navigator.platform,
          language: navigator.language,
          cookieEnabled: navigator.cookieEnabled
        },
        screenInfo: {
          width: window.screen.width,
          height: window.screen.height,
          devicePixelRatio: window.devicePixelRatio
        }
      });
      
    } catch (error) {
      console.error('Debug test failed:', error);
    }
    
    setIsDebugging(false);
  };

  return (
    <div className="p-6 bg-gray-100 rounded-lg">
      <h2 className="text-xl font-bold mb-4">🔍 WebRTC Debug Panel</h2>
      
      <button 
        onClick={runDebugTests}
        disabled={isDebugging}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {isDebugging ? 'Running Tests...' : 'Run Debug Tests'}
      </button>
      
      {Object.keys(debugInfo).length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold mb-2">Debug Results:</h3>
          <pre className="bg-white p-4 rounded text-sm overflow-auto max-h-96">
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
```

### **Step 7: Add Debug Panel to Your App**

Add the debug panel to your main page:

```tsx
// In your main page component
import { WebRTCDebugPanel } from '@/components/debug/WebRTCDebugPanel';

export default function DebugPage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">WebRTC Debug Environment</h1>
      <WebRTCDebugPanel />
    </div>
  );
}
```

---

## 🚀 **Debug Workflow**

### **Step 8: Complete Debug Session**

1. **Start Servers**:
   ```bash
   # Terminal 1: Frontend
   cd frontend && npm run dev
   
   # Terminal 2: Backend  
   cd backend && python run_with_venv.py
   ```

2. **Open Debug Environment**:
   - Go to `http://localhost:3000/debug` (or wherever you added the debug panel)
   - Open Chrome DevTools (F12)
   - Go to Sources tab and set breakpoints in your WebRTC code

3. **Run Debug Tests**:
   - Click "Run Debug Tests" button
   - Watch console output for detailed debugging info
   - Check breakpoints in VSCode debugger

4. **Test Different Scenarios**:
   - Desktop Chrome: Normal user agent
   - Mobile simulation: Change user agent in DevTools
   - Different browsers: Test in Safari, Firefox
   - Network conditions: Throttle network in DevTools

### **Step 9: Mobile Testing**

Test mobile detection with Chrome DevTools:

1. Open DevTools (F12)
2. Click device toolbar icon (mobile/tablet icon)
3. Select different devices (iPhone, iPad, Android)
4. Reload page and check console output
5. Verify mobile-specific constraints are applied

---

## 📊 **Expected Debug Output**

You should see console output like this:

```
🔍 [DEBUG] User Agent: mozilla/5.0 (iphone; cpu iphone os 14_7_1 like mac os x)...
🔍 [DEBUG] Mobile keyword found: iphone
🔍 [DEBUG] Is Mobile Browser: true
🔍 [DEBUG] Detected Keywords: ["iphone", "mobile"]

🔍 [DEBUG] Browser Capabilities Analysis
  User Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1...)
  Platform: iPhone
  Is Mobile: true
  Browser Detection: {chrome: false, safari: true, firefox: false, edge: false}
  WebRTC Support: {getUserMedia: true, RTCPeerConnection: true}

🔍 [DEBUG] Universal Constraints Generation
  Browser Detection: {isChrome: false, isSafari: true, isFirefox: false, isMobile: true}
  Generated Constraints: {
    "audio": {
      "echoCancellation": true,
      "noiseSuppression": true,
      "autoGainControl": true,
      "webkitEchoCancellation": true,
      "webkitNoiseSuppression": true,
      "webkitAutoGainControl": true,
      "latency": {"ideal": 0.01, "max": 0.02},
      "sampleRate": {"ideal": 48000},
      "channelCount": {"ideal": 1, "max": 1}
    }
  }
```

This debug setup will help you thoroughly test and understand how your Universal WebRTC Compatibility system works across different browsers and devices!
