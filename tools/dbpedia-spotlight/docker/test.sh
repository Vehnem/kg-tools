#!/bin/bash

# Test the spotlight service
curl -i -X POST http://localhost:2222/rest/annotate -H "Accept: application/json" -d "text=The capital of France is Paris"

# Test the spotlight service with a file
# curl -X POST http://localhost:2222/rest/annotate -H "Content-Type: application/x-www-form-urlencoded" -d "text=The capital of France is Paris"
