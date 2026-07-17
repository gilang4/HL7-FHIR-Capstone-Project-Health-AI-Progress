    # --- 1. CONFIGURATION ---
    # Paste Epic Client ID here

$clientId = "7defd2fb-f768-4196-8e1a-bebae4975b68"


    # This MUST match the Redirect URI saved in Epic
$redirectUri = "https://oauth.pstmn.io/v1/callback"

    # Scopes required for Python script to read Encounters and write DocumentReferences
    # Change this line in your PowerShell script:
$scopes = "openid user/Patient.read user/Encounter.read user/DocumentReference.write"
# $scopes = "openid fhirUser launch/patient patient/Patient.read patient/Encounter.read patient/DocumentReference.write"

    # Epic Endpoints
$authBaseUrl = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"
$tokenUrl    = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"

    # --- 2. OPEN BROWSER FOR LOGIN ---
    # Construct the full authorization URL
$encodedRedirect = [System.Uri]::EscapeDataString($redirectUri)

$encodedScopes   = [System.Uri]::EscapeDataString($scopes)

$fullAuthUrl = "$($authBaseUrl)?response_type=code&client_id=$($clientId)&redirect_uri=$($encodedRedirect)&scope=$($encodedScopes)&state=12345"

    # ADD THIS LINE RIGHT HERE:
Write-Host "DEBUG URL: $fullAuthUrl" -ForegroundColor Magenta


Write-Host "Opening your default browser to log in to Epic..." -ForegroundColor Cyan
Start-Process $fullAuthUrl

# --- 3. GET THE AUTHORIZATION CODE ---
Write-Host "`n--- INSTRUCTIONS ---" -ForegroundColor Yellow
Write-Host "1. Log in to Epic in your browser." -ForegroundColor Yellow
Write-Host "2. Select a patient (e.g., Theodore Mychart) and click 'Allow'." -ForegroundColor Yellow
Write-Host "3. The browser will redirect to a blank Postman page." -ForegroundColor Yellow
Write-Host "4. Look at the URL in the browser's address bar. It will look like:" -ForegroundColor Yellow
Write-Host "   https://oauth.pstmn.io/v1/callback?code=A12b34C...&state=12345" -ForegroundColor Yellow
Write-Host "5. Copy the long code AFTER 'code=' and BEFORE '&state='." -ForegroundColor Yellow

$authCode = Read-Host "`nPaste the Authorization Code here"

# --- 4. EXCHANGE CODE FOR ACCESS TOKEN ---
Write-Host "`nExchanging code for an Access Token..." -ForegroundColor Cyan

$body = @{
    grant_type   = "authorization_code"
    code         = $authCode.Trim() # Trim any accidental spaces
    redirect_uri = $redirectUri
    client_id    = $clientId
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    
    Write-Host "`n✅ SUCCESS! Token generated." -ForegroundColor Green
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "ACCESS TOKEN:" -ForegroundColor White
    Write-Host $tokenResponse.access_token -ForegroundColor Yellow
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "PATIENT ID (from token):" -ForegroundColor White
    Write-Host $tokenResponse.patient -ForegroundColor Yellow
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
            
        # Optional: Save the token to a text file so you don't have to copy-paste it manually
    $tokenResponse.access_token | Out-File -FilePath "epic_token.txt" -NoNewline
    Write-Host "`n💾 Token also saved to 'epic_token.txt' in this folder." -ForegroundColor Cyan

} catch {
    Write-Error "❌ Failed to get token. Check your Client ID and the code you pasted."
    Write-Error "Error details: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) {
        Write-Error "Epic response: $($_.ErrorDetails.Message)"
    }
}