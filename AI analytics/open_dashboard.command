#!/bin/bash
cd "$(dirname "$0")"
python3 -m http.server 8080 &
# Wait a moment for the server to start
sleep 2
open "http://localhost:8080/Complete_Inventory_Dashboard.html" 