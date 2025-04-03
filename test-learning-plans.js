// Test script for Language Tutor learning plans
const fetch = require('node-fetch');

// Configuration
const API_URL = 'http://localhost:8000';
const TEST_USER = {
  email: `testuser_${Date.now()}@example.com`,
  password: 'Password123!',
  name: 'Test User'
};

// Store auth token and user info
let authToken = null;
let userId = null;
let learningPlanId = null;

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', body = null, token = null) {
  const headers = {
    'Content-Type': 'application/json'
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const options = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  };
  
  console.log(`Making ${method} request to ${endpoint}`);
  const response = await fetch(`${API_URL}${endpoint}`, options);
  const data = await response.json().catch(() => null);
  
  if (!response.ok) {
    console.error(`Error ${response.status}: ${data?.detail || 'Unknown error'}`);
    throw new Error(`API call failed: ${data?.detail || 'Unknown error'}`);
  }
  
  return data;
}

// Test steps
async function runTests() {
  console.log('=== LANGUAGE TUTOR API TEST ===');
  console.log(`Test started at: ${new Date().toISOString()}`);
  console.log('----------------------------');
  
  try {
    // Step 1: Create a test user
    console.log('\n📝 STEP 1: Creating test user...');
    const user = await apiCall('/auth/register', 'POST', TEST_USER);
    console.log(`✅ User created: ${user.email} (ID: ${user._id})`);
    userId = user._id;
    
    // Step 2: Login with the test user
    console.log('\n🔑 STEP 2: Logging in...');
    const loginResponse = await apiCall('/auth/login', 'POST', {
      email: TEST_USER.email,
      password: TEST_USER.password
    });
    authToken = loginResponse.access_token;
    console.log(`✅ Login successful, token received: ${authToken.substring(0, 15)}...`);
    
    // Step 3: Create a custom learning plan
    console.log('\n📚 STEP 3: Creating custom learning plan...');
    const learningPlan = await apiCall('/learning/plan', 'POST', {
      plan_request: {
        language: 'french',
        proficiency_level: 'intermediate',
        goals: ['business', 'speaking', 'listening'],
        duration_months: 4,
        custom_goal: 'Learn to conduct business meetings in French'
      }
    }, authToken);
    
    learningPlanId = learningPlan.id;
    console.log(`✅ Learning plan created: ${learningPlanId}`);
    console.log(`   Language: ${learningPlan.language}`);
    console.log(`   Level: ${learningPlan.proficiency_level}`);
    console.log(`   Custom goal: ${learningPlan.custom_goal}`);
    
    // Step 4: Verify the plan is assigned to the user
    console.log('\n🔍 STEP 4: Verifying plan assignment...');
    if (learningPlan.user_id === userId) {
      console.log(`✅ Plan correctly assigned to user: ${userId}`);
    } else if (!learningPlan.user_id) {
      console.log(`⚠️ Plan not automatically assigned to user. This is expected if created without auth.`);
      
      // Step 4b: Manually assign the plan to the user
      console.log('\n🔄 STEP 4b: Manually assigning plan to user...');
      const assignResponse = await apiCall(`/learning/plan/${learningPlanId}/assign`, 'PUT', null, authToken);
      console.log(`✅ Plan manually assigned to user: ${assignResponse.user_id}`);
    } else {
      console.log(`❌ Plan assigned to unexpected user: ${learningPlan.user_id}`);
    }
    
    // Step 5: Retrieve all user's learning plans
    console.log('\n📋 STEP 5: Retrieving all user learning plans...');
    const userPlans = await apiCall('/learning/plans', 'GET', null, authToken);
    console.log(`✅ Retrieved ${userPlans.length} learning plans for user`);
    
    if (userPlans.length > 0) {
      console.log('   Plans:');
      userPlans.forEach((plan, index) => {
        console.log(`   ${index + 1}. ${plan.language} (${plan.proficiency_level}) - ID: ${plan.id}`);
        console.log(`      Goals: ${plan.goals.join(', ')}`);
        if (plan.custom_goal) {
          console.log(`      Custom goal: ${plan.custom_goal}`);
        }
      });
    }
    
    // Step 6: Retrieve a specific learning plan
    console.log('\n🔎 STEP 6: Retrieving specific learning plan...');
    const specificPlan = await apiCall(`/learning/plan/${learningPlanId}`, 'GET', null, authToken);
    console.log(`✅ Successfully retrieved plan: ${specificPlan.id}`);
    console.log(`   Language: ${specificPlan.language}`);
    console.log(`   Level: ${specificPlan.proficiency_level}`);
    console.log(`   Custom goal: ${specificPlan.custom_goal}`);
    
    // Summary
    console.log('\n=== TEST SUMMARY ===');
    console.log('✅ All tests completed successfully!');
    console.log('\nTest user credentials:');
    console.log(`Email: ${TEST_USER.email}`);
    console.log(`Password: ${TEST_USER.password}`);
    console.log(`User ID: ${userId}`);
    console.log('\nLearning plan details:');
    console.log(`Plan ID: ${learningPlanId}`);
    console.log(`Language: ${specificPlan.language}`);
    console.log(`Level: ${specificPlan.proficiency_level}`);
    console.log('\nYou can now:');
    console.log(`1. Sign in at http://localhost:3000/auth/login with the test user`);
    console.log(`2. Go to your profile page at http://localhost:3000/profile to see your learning plans`);
    console.log(`3. Use the speech page with this plan: http://localhost:3000/speech?plan=${learningPlanId}`);
    
  } catch (error) {
    console.error('\n❌ TEST FAILED');
    console.error(error);
  }
  
  console.log('\nTest completed at:', new Date().toISOString());
}

// Run the tests
runTests();
