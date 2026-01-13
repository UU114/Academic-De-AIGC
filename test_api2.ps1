# Test Step 4.1 API - check paragraph data
Write-Host "Testing Step 4.1 Pattern Analysis API..."

try {
    $body = '{"text": "Climate change is crucial. It is essential to understand. The impact was significant.\n\nThis paper explores the topic. We analyze the data carefully. Results show important findings.", "session_id": "test-new-session-xyz"}'
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/analysis/sentence/step4-1/pattern' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing -TimeoutSec 120
    $json = ConvertFrom-Json $response.Content

    Write-Host "risk_score: $($json.risk_score)"
    Write-Host "risk_level: $($json.risk_level)"
    Write-Host "high_risk_paragraphs count: $($json.high_risk_paragraphs.Count)"
    Write-Host ""
    Write-Host "Paragraph Details:"
    foreach ($p in $json.high_risk_paragraphs) {
        Write-Host "  Para $($p.paragraph_index): Score=$($p.risk_score), Level=$($p.risk_level), SimpleRatio=$($p.simple_ratio), LengthCV=$($p.length_cv), OpenerRep=$($p.opener_repetition)"
    }

    Write-Host ""
    Write-Host "Test completed!"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}
