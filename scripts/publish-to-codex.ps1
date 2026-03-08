param(
    [string]$SkillName,
    [switch]$All,
    [string]$RepoRoot,
    [string]$DestinationRoot
)

$ErrorActionPreference = "Stop"

 function Resolve-RepoRoot {
     param([string]$ExplicitRoot)
     if ($ExplicitRoot) {
         return (Resolve-Path $ExplicitRoot).Path
     }
    $scriptRoot = $PSScriptRoot
    if (-not $scriptRoot) {
        $scriptRoot = Split-Path -Parent $PSCommandPath
    }
     return (Resolve-Path (Join-Path $scriptRoot "..")).Path
 }

function Ensure-Directory {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue | Out-Null
    }
}

function Copy-DirectoryContents {
    param(
        [string]$SourceDir,
        [string]$TargetDir
    )
    if (-not (Test-Path $SourceDir)) {
        return
    }
    Ensure-Directory -PathValue $TargetDir
    Copy-Item -Path (Join-Path $SourceDir "*") -Destination $TargetDir -Recurse -Force
}

function Publish-Skill {
    param(
        [string]$SkillDir,
        [string]$TargetRoot
    )
    $skillName = Split-Path $SkillDir -Leaf
    $sharedDir = Join-Path $SkillDir "shared"
    $codexDir = Join-Path $SkillDir "codex"
    $targetDir = Join-Path $TargetRoot $skillName
    $tempDir = Join-Path $TargetRoot (".$skillName.tmp")

    if (-not (Test-Path $sharedDir)) {
        throw "Missing shared directory for skill: $skillName"
    }
    if (-not (Test-Path $codexDir)) {
        throw "Missing codex adapter directory for skill: $skillName"
    }

    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir
    }
    Ensure-Directory -PathValue $tempDir

    Copy-DirectoryContents -SourceDir $sharedDir -TargetDir $tempDir
    Copy-DirectoryContents -SourceDir $codexDir -TargetDir $tempDir

    if (Test-Path $targetDir) {
        Remove-Item -Recurse -Force $targetDir
    }
    Move-Item -Path $tempDir -Destination $targetDir
    Write-Host "Published $skillName -> $targetDir"
}

function Get-SkillDirectories {
    param([string]$SkillsRoot)
    Get-ChildItem -Path $SkillsRoot -Directory -Recurse |
        Where-Object {
            (Test-Path (Join-Path $_.FullName "shared")) -and
            (Test-Path (Join-Path $_.FullName "codex"))
        } |
        Sort-Object FullName
}

function Resolve-SkillDirectory {
    param(
        [string]$SkillsRoot,
        [string]$RequestedSkill
    )

    $direct = Join-Path $SkillsRoot $RequestedSkill
    if ((Test-Path (Join-Path $direct "shared")) -and (Test-Path (Join-Path $direct "codex"))) {
        return (Get-Item $direct)
    }

    $matches = Get-ChildItem -Path $SkillsRoot -Directory -Recurse |
        Where-Object { $_.Name -eq $RequestedSkill } |
        Where-Object {
            (Test-Path (Join-Path $_.FullName "shared")) -and
            (Test-Path (Join-Path $_.FullName "codex"))
        } |
        Sort-Object FullName

    if ($matches.Count -eq 1) {
        return $matches[0]
    }
    if ($matches.Count -gt 1) {
        throw "Multiple skills matched '$RequestedSkill'. Use a category-qualified path."
    }

    throw "Skill not found: $RequestedSkill"
}

$resolvedRepoRoot = Resolve-RepoRoot -ExplicitRoot $RepoRoot
$skillsRoot = Join-Path $resolvedRepoRoot "skills"

if (-not (Test-Path $skillsRoot)) {
    throw "Skills directory not found: $skillsRoot"
}

if (-not $DestinationRoot) {
    $homeDir = $env:USERPROFILE
    if (-not $homeDir) {
        $homeDir = $HOME
    }
    $DestinationRoot = Join-Path $homeDir ".codex\skills"
}

Ensure-Directory -PathValue $DestinationRoot

if ($All) {
    $skillDirs = Get-SkillDirectories -SkillsRoot $skillsRoot
} elseif ($SkillName) {
    $skillDirs = @(Resolve-SkillDirectory -SkillsRoot $skillsRoot -RequestedSkill $SkillName)
} else {
    throw "Provide -SkillName <name> or use -All"
}

foreach ($skillDir in $skillDirs) {
    Publish-Skill -SkillDir $skillDir.FullName -TargetRoot $DestinationRoot
}

Write-Host "Done. Restart Codex to reload installed skills."
