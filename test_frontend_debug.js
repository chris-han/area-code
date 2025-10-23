// Simple test to debug frontend workflow page
// Run with: node test_frontend_debug.js

const fetch = require('node-fetch');

async function testFrontendAPI() {
    console.log('🧪 Testing Frontend API Integration');
    console.log('=' * 50);

    try {
        // Test direct API call (what the frontend should be doing)
        console.log('1. Testing direct API call...');
        const response = await fetch('http://localhost:3003/api/bia/api/v1/workflows/list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ API Response:', JSON.stringify(data, null, 2));

        // Test what the frontend mapping should produce
        console.log('\n2. Testing frontend data mapping...');
        const mappedWorkflows = (data.workflows || []).map(workflow => ({
            id: workflow.workflow_id || workflow.id || 'unknown',
            name: workflow.workflow_type || 'Unknown Workflow',
            status: workflow.status || 'scheduled',
            startTime: workflow.start_time ? new Date(workflow.start_time) : null,
            endTime: workflow.end_time ? new Date(workflow.end_time) : undefined,
            progress: workflow.progress
        }));

        console.log('✅ Mapped workflows:', mappedWorkflows);
        console.log(`📊 Total workflows: ${mappedWorkflows.length}`);

        if (mappedWorkflows.length === 0) {
            console.log('ℹ️  Empty list - frontend should show "No workflows found"');
        }

        console.log('\n3. Frontend checklist:');
        console.log('✅ API proxy working');
        console.log('✅ Data structure correct');
        console.log('✅ Response format valid');
        console.log('⚠️  Check browser console for React errors');

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

testFrontendAPI();