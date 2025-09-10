# VSCode Debugging Instructions for WebRTC Mobile Detection

## Step 1: Access the VSCode Debugger
1. In VSCode, click on the **Run and Debug** icon in the left sidebar (looks like a play button with a bug)
   - Or use keyboard shortcut: `Cmd+Shift+D` (Mac) or `Ctrl+Shift+D` (Windows/Linux)

## Step 2: Select Debug Configuration
1. At the top of the Debug panel, you'll see a dropdown menu
2. Select **"Debug Frontend (Chrome)"** from the dropdown
3. You should see the green play button next to it

## Step 3: Start Debugging Session
1. Click the green **play button** (▶️) or press `F5`
2. This will:
   - Launch a new Chrome window with debugging enabled
   - Navigate to http://localhost:3000
   - Connect VSCode debugger to the Chrome instance

## Step 4: Set Breakpoints
1. Open `frontend/lib/enhancedRealtimeService.ts` in VSCode
2. Find the `isMobileBrowser()` function (around line where it's defined)
3. Click in the left margin (gutter) next to the line numbers to set breakpoints:
   - Set a breakpoint on the line: `const userAgent = window.navigator.userAgent.toLowerCase();`
   - Set another on: `const result = mobileKeywords.some(keyword => userAgent.includes(keyword));`

## Step 5: Trigger the Function
1. In the Chrome window that opened, interact with your app to trigger the WebRTC functionality
2. The debugger should pause at your breakpoints
3. You can inspect variables, step through code, and see the call stack

## Step 6: Test Mobile Simulation
1. In the Chrome debugging window, press `F12` to open DevTools
2. Click the device toggle icon (📱) or press `Ctrl+Shift+M`
3. Select a mobile device from the dropdown
4. Refresh the page to trigger the mobile detection again

## Troubleshooting
- Make sure your frontend server is running on http://localhost:3000
- If Chrome doesn't open, check that Chrome is installed and accessible
- If breakpoints don't hit, make sure source maps are enabled in your build
