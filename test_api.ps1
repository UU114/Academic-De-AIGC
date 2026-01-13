# Test Step 4.1 API
Write-Host "Testing Step 4.1 Pattern Analysis API..."

try {
    $body = '{"text": "Climate change is crucial. It is essential. The impact was significant.", "session_id": "e1ad7382-5eb8-4866-a209-2e5775a7b728"}'
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/analysis/sentence/step4-1/pattern' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing -TimeoutSec 120
    $json = ConvertFrom-Json $response.Content

    Write-Host "risk_score: $($json.risk_score)"
    Write-Host "risk_level: $($json.risk_level)"
    Write-Host "high_risk_count: $($json.high_risk_paragraphs.Count)"

    foreach ($p in $json.high_risk_paragraphs) {
        Write-Host "  Para $($p.paragraph_index): Risk=$($p.risk_score), Level=$($p.risk_level)"
    }

    Write-Host "Test completed successfully!"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}
