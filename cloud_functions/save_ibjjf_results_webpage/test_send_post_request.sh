curl -m 70 -X POST localhost:8080 -H "Authorization: bearer $(gcloud auth print-identity-token)" -H "Content-Type: application/json" -d '{
  "url": "https://ibjjf.com/events/results"
}'
