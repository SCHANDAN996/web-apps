$ErrorActionPreference='Stop'
$memoryRoot=Split-Path $PSScriptRoot -Parent
$manifest=Get-Content -LiteralPath (Join-Path $memoryRoot 'manifest.json') -Raw | ConvertFrom-Json
$sections=@('START-HERE.md','UPDATE-PROMPT.md','agents/ROUTING.md','agents/ACTION-PLAN.md','protocols/CHAT-RECORD.md','chats/INDEX.md','memory/PROFILE.md','memory/CURRENT.md','memory/BEHAVIOUR.md','memory/IDEAS.md','memory/OPEN-QUESTIONS.md','protocols/UPDATE.md','legacy/family/README.md','sources/COVERAGE.md','reviews/PROJECT-TIMELINE.md','PLAN.md','CHANGELOG.md')
$out=[Collections.Generic.List[string]]::new()
$out.Add('# चंदन — मेरी डिजिटल स्मृति, एक फ़ाइल')
$out.Add('निजी working snapshot · revision '+$manifest.revision+' · '+$manifest.updated_at+' · इसे परिवार के लिए स्वतः अनुमोदित सामग्री न मानें।')
$out.Add('इसी एक फ़ाइल से दूसरी chat संदर्भ समझ सकती है। update माँगे जाने पर source section के अनुसार सुधार दें; लिखने की पहुँच न हो तो revised फ़ाइल लौटाएँ। मुख्य folder की नई copy मिले तो source files से merge करें, पुराना snapshot उन पर न चढ़ाएँ। यह file model training या automatic sync नहीं करती।')
foreach($section in $sections){$out.Add('');$out.Add('---');$out.Add('स्रोत फ़ाइल: '+$section);$out.Add('');$out.Add((Get-Content -LiteralPath (Join-Path $memoryRoot $section) -Raw))}
$out.Add('');$out.Add('## व्यवहार घटनाएँ — source records');$out.Add('```jsonl');$out.Add((Get-Content -LiteralPath (Join-Path $memoryRoot 'memory/EPISODES.jsonl') -Raw));$out.Add('```')
$outputPath=Join-Path $memoryRoot 'MY-DIGITAL-MEMORY.md'
$out | Set-Content -LiteralPath $outputPath -Encoding utf8
Write-Output $outputPath
