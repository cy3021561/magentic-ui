#!/usr/bin/env python3
"""
Simple test script to quickly send data to the Vision Assistant WebSocket client
"""

import asyncio
import websockets
import json
import ssl
import time

# WebSocket URL
WEBSOCKET_URL = "wss://7b56-98-154-38-6.ngrok-free.app/connect-user/user"

# Simple test data
TEST_DATA = [
{
    "personal_information": {
        "provider_information": {
            "name": [
                {
                    "bbox": [
                        508,
                        87,
                        1106,
                        123
                    ],
                    "text": "Huntington Health",
                    "confidence": 1
                }
            ]
        },
        "doctor_information": {
            "unit": [
                {
                    "bbox": [
                        1531,
                        399,
                        1568,
                        429
                    ],
                    "text": "IP",
                    "confidence": 1
                }
            ],
            "att_physician": [
                {
                    "bbox": [
                        409,
                        994,
                        775,
                        1031
                    ],
                    "text": "Lev Gertsik",
                    "confidence": 1
                }
            ],
            "adm_physician": [
                {
                    "bbox": [
                        411,
                        962,
                        775,
                        997
                    ],
                    "text": "Lev Gertsik",
                    "confidence": 1
                }
            ]
        },
        "patient_information": {
            "first_name": [
                {
                    "bbox": [
                        172,
                        344,
                        315,
                        379
                    ],
                    "text": "Lisa",
                    "confidence": 1
                }
            ],
            "last_name": [
                {
                    "bbox": [
                        172,
                        344,
                        315,
                        379
                    ],
                    "text": "Silina",
                    "confidence": 1
                }
            ],
            "address": [
                {
                    "bbox": [
                        179,
                        383,
                        352,
                        420
                    ],
                    "text": "123 Default Ave",
                    "confidence": 1
                }
            ],
            "zip_code": [
                {
                    "bbox": [
                        175,
                        449,
                        442,
                        484
                    ],
                    "text": "90048",
                    "confidence": 1
                }
            ],
            "legal_sex": [
                {
                    "bbox": [
                        457,
                        524,
                        469,
                        538
                    ],
                    "text": "female",
                    "confidence": 1
                }
            ],
            "birthdate": [
                {
                    "bbox": [
                        172,
                        518,
                        276,
                        543
                    ],
                    "text": "08/03/1988",
                    "confidence": 1
                }
            ]
        },
        "insurance_information": {
            "payor_name_0": [
                {
                    "bbox": [
                        204,
                        1436,
                        439,
                        1471
                    ],
                    "text": "BRMS",
                    "confidence": 1
                }
            ],
            "subscriber_id_0": [
                {
                    "bbox": [
                        207,
                        1564,
                        264,
                        1580
                    ],
                    "text": "0254348",
                    "confidence": 1
                }
            ]
        }
    },
    "encounter_information": {
        "updated_treatment_activities": [
            {
                "service_date": "10/02/2024",
                "hcpc_code": "99223"
            }
        ],
        "updated_icd10": [
            {
                "icd10_code": "F90.9"
            },
            {
                "icd10_code": "F41.9"
            },
            {
                "icd10_code": "G47.09"
            }
        ]
    },
    "selected_emr": "office_ally",
    "page_id": "694a48fa20d2eec46b2101552c9e4798decbe6e65f3a083de253bc504ef8f4a4"
}
]

async def send_test():
    """Send test data to the WebSocket client"""
    
    # Create SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        print(f"🔌 Connecting to {WEBSOCKET_URL}...")
        
        async with websockets.connect(WEBSOCKET_URL, ssl=ssl_context) as websocket:
            print("✅ Connected!")
            
            # Send test data
            print("📤 Sending test data...")
            await websocket.send(json.dumps(TEST_DATA))
            print("✅ Data sent!")
            
            # Listen for a few responses
            print("📥 Listening for responses...")
            for i in range(5):  # Listen for up to 5 responses
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    print(f"📨 Response {i+1}: {response_data.get('executed_action', 'N/A')} - {response_data.get('type', 'N/A')}")
                    
                    if response_data.get('type') in ['all_done', 'critical']:
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ No more responses")
                    break
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Simple Vision Assistant Test")
    print("Hold 3 seconds before running the client")
    time.sleep(3)
    print("Make sure the client is running: python -m src.client.client")
    print()
    
    asyncio.run(send_test()) 