#!/usr/bin/env python3
"""
Test script to check if the plan.list and plan.read JSON-RPC endpoints are working
"""
import asyncio
import websockets
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_plan_endpoints():
    """Test the plan endpoints via WebSocket JSON-RPC"""
    
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Test plan.list
            logger.info("Testing plan.list...")
            plan_list_request = {
                "jsonrpc": "2.0",
                "method": "plan.list",
                "params": {},
                "id": 1
            }
            
            await websocket.send(json.dumps(plan_list_request))
            response = await websocket.recv()
            list_result = json.loads(response)
            
            logger.info(f"plan.list response: {json.dumps(list_result, indent=2)}")
            
            # If we got plans, test plan.read on the first one
            if "result" in list_result and "plans" in list_result["result"] and list_result["result"]["plans"]:
                plans = list_result["result"]["plans"]
                if len(plans) > 0:
                    # Get the first plan name
                    first_plan = plans[0]
                    plan_name = None
                    
                    # Try different possible keys for plan name
                    for key in ["plan_name", "name", "_plan_name"]:
                        if key in first_plan:
                            plan_name = first_plan[key]
                            break
                    
                    if plan_name:
                        logger.info(f"Testing plan.read with plan_name: {plan_name}")
                        plan_read_request = {
                            "jsonrpc": "2.0",
                            "method": "plan.read",
                            "params": {"plan_name": plan_name},
                            "id": 2
                        }
                        
                        await websocket.send(json.dumps(plan_read_request))
                        response = await websocket.recv()
                        read_result = json.loads(response)
                        
                        logger.info(f"plan.read response: {json.dumps(read_result, indent=2)}")
                    else:
                        logger.warning(f"Could not find plan name in first plan: {first_plan}")
                else:
                    logger.warning("No plans found in response")
            else:
                logger.warning("No plans found or unexpected response format")
                
    except Exception as e:
        logger.error(f"Error testing endpoints: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_plan_endpoints())
