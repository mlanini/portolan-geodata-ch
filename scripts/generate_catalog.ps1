param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$proxy = 'http://proxy-bvcol.admin.ch:8080'
$scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$repoRoot = if ($PSScriptRoot) { Resolve-Path (Join-Path $scriptRoot '..') } else { (Get-Location).Path }
$siteUrl = 'https://data.geo.ti.ch/'
$geoportaleUrl = 'https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/home'
$mapUrl = 'https://map.geo.ti.ch/'
$conditionsUrl = 'https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/geoportale/condizioni-utilizzo'

function ConvertTo-Slug {
    param([Parameter(Mandatory)] [string]$Value)
    $slug = $Value.ToLowerInvariant()
    $slug = $slug -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    return $slug
}

function Get-CategoryFolder {
    param([Parameter(Mandatory)] [string]$Code)

    if ($Code -eq 'CH-mu') { return 'ch-base' }
    if ($Code.StartsWith('CH-041.6') -or $Code.StartsWith('CH-041.7')) { return 'ch-raster' }
    if ($Code.StartsWith('CH-')) { return 'ch-base' }
    if ($Code.StartsWith('TI-')) { return 'ti-base' }
    if ($Code.StartsWith('AC-')) { return 'ac' }

    throw "Unsupported dataset code: $Code"
}

function HtmlDecode {
    param([Parameter(Mandatory)] [string]$Value)
    return [System.Net.WebUtility]::HtmlDecode($Value).Trim()
}

function New-JsonFile {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] $Value
    )

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    $json = $Value | ConvertTo-Json -Depth 20
    Set-Content -Path $Path -Value $json -Encoding utf8
}

$html = (Invoke-WebRequest -Uri $siteUrl -UseBasicParsing -Proxy $proxy).Content
$pattern = '<tr>\s*<td width="30%"><a href="\?p=([^"]+)">([^<]+)</a></td>\s*<td width="30%">([^<]+)</td>\s*<td width="40%">([^<]+)</td>\s*</tr>'
$matches = [regex]::Matches($html, $pattern, 'Singleline')

$pathOverrides = @{
    'CH-063.1' = 'ch-base/ch-063-1-suddivisioni-amministrative'
    'CH-181.1' = 'ch-base/ch-181-1-cap-localita'
    'TI-028b.1' = 'ti-base/ti-028b-1-piani-regolatori'
    'TI-034.1' = 'ti-base/ti-034-1-carta-pericoli-gradi'
    'AC-009.1' = 'ac/ac-009-1-piano-direttore-cantonale'
    'AC-077.1' = 'ac/ac-077-1-repertorio-toponomastico-ticinese'
    'CH-041.6' = 'ch-raster/ch-041-6r-swissalti3d'
    'CH-041.7' = 'ch-raster/ch-041-7r-swisssurface3d'
    'CH-041.6R' = 'ch-raster/ch-041-6r-swissaltiregio'
}

$datasets = foreach ($match in $matches) {
    $code = HtmlDecode $match.Groups[2].Value
    $version = HtmlDecode $match.Groups[3].Value
    $title = HtmlDecode $match.Groups[4].Value
    $page = HtmlDecode $match.Groups[1].Value
    $categoryFolder = Get-CategoryFolder -Code $code
    [pscustomobject]@{
        code = $code
        version = $version
        title = $title
        page = $page
        categoryFolder = $categoryFolder
    }
}

$datasets = $datasets | Sort-Object categoryFolder, code

$datasetRecords = foreach ($dataset in $datasets) {
    $relativePath = if ($pathOverrides.ContainsKey($dataset.code)) {
        $pathOverrides[$dataset.code]
    } else {
        (Join-Path $dataset.categoryFolder (ConvertTo-Slug $dataset.code))
    }

    $collectionPath = Join-Path $repoRoot $relativePath
    [pscustomobject]@{
        code = $dataset.code
        version = $dataset.version
        title = $dataset.title
        page = $dataset.page
        categoryFolder = $dataset.categoryFolder
        relativePath = $relativePath.Replace('\', '/')
        collectionPath = $collectionPath
    }
}

$categoryDefinitions = [ordered]@{
    'ch-base' = [ordered]@{
        title = 'CH - Geodati di base di diritto federale, competenza cantonale'
        description = 'Catalogo dei geodati CH pubblicati da data.geo.ti.ch.'
    }
    'ti-base' = [ordered]@{
        title = 'TI - Geodati di base di diritto cantonale'
        description = 'Catalogo dei geodati TI pubblicati da data.geo.ti.ch.'
    }
    'ac' = [ordered]@{
        title = 'AC - Geodati dell''Amministrazione cantonale'
        description = 'Catalogo dei geodati AC pubblicati da data.geo.ti.ch.'
    }
    'ch-raster' = [ordered]@{
        title = 'CH - Geodati raster (Cloud Optimized GeoTIFF)'
        description = 'Catalogo dei geodati raster CH pubblicati da data.geo.ti.ch.'
    }
}

foreach ($category in $categoryDefinitions.Keys) {
    $categoryItems = $datasetRecords | Where-Object { $_.categoryFolder -eq $category }
    $categoryPath = Join-Path $repoRoot $category
    New-Item -ItemType Directory -Force -Path $categoryPath | Out-Null

    $categoryLinks = @(
        [ordered]@{ rel = 'root'; href = '../catalog.json'; type = 'application/json' },
        [ordered]@{ rel = 'parent'; href = '../catalog.json'; type = 'application/json' },
        [ordered]@{ rel = 'self'; href = './catalog.json'; type = 'application/json' }
    )

    foreach ($item in $categoryItems) {
        $leaf = $item.relativePath.Substring($category.Length + 1)
        $categoryLinks += [ordered]@{
            rel = 'child'
            href = "./$leaf/collection.json"
            type = 'application/json'
            title = "$($item.code) - $($item.title)"
        }
    }

    $categoryCatalog = [ordered]@{
        type = 'Catalog'
        stac_version = '1.1.0'
        id = $category
        title = $categoryDefinitions[$category].title
        description = $categoryDefinitions[$category].description
        links = $categoryLinks
    }

    New-JsonFile -Path (Join-Path $categoryPath 'catalog.json') -Value $categoryCatalog
}

$rootCatalog = [ordered]@{
    type = 'Catalog'
    stac_version = '1.1.0'
    stac_extensions = @('https://schemas.portolan-sdi.org/portolan/v0.2.0/schema.json')
    id = 'geodata-ch-ti-complete'
    title = 'Portolan Geodata CH/TI - catalogo completo data.geo.ti.ch'
    description = "Catalogo STAC completo dei geodati del portale data.geo.ti.ch, ricavato dall'indice ufficiale e arricchito con riferimenti del Geoportale Ticino e di map.geo.ti.ch."
    updated = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    links = @(
        [ordered]@{ rel = 'root'; href = './catalog.json'; type = 'application/json' },
        [ordered]@{ rel = 'self'; href = './catalog.json'; type = 'application/json' },
        [ordered]@{ rel = 'child'; href = './ch-base/catalog.json'; type = 'application/json'; title = $categoryDefinitions['ch-base'].title },
        [ordered]@{ rel = 'child'; href = './ti-base/catalog.json'; type = 'application/json'; title = $categoryDefinitions['ti-base'].title },
        [ordered]@{ rel = 'child'; href = './ac/catalog.json'; type = 'application/json'; title = $categoryDefinitions['ac'].title },
        [ordered]@{ rel = 'child'; href = './ch-raster/catalog.json'; type = 'application/json'; title = $categoryDefinitions['ch-raster'].title },
        [ordered]@{ rel = 'related'; href = $geoportaleUrl; type = 'text/html'; title = 'Geoportale Ticino' },
        [ordered]@{ rel = 'related'; href = $mapUrl; type = 'text/html'; title = 'Geoportale Ticino - Mappa' },
        [ordered]@{ rel = 'related'; href = $conditionsUrl; type = 'text/html'; title = 'Condizioni di utilizzo' },
        [ordered]@{ rel = 'related'; href = $siteUrl; type = 'text/html'; title = 'Portale per il download dei geodati' },
        [ordered]@{ rel = 'describedby'; href = './README.md'; type = 'text/markdown'; title = 'Human-readable documentation' }
    )
}

New-JsonFile -Path (Join-Path $repoRoot 'catalog.json') -Value $rootCatalog

foreach ($item in $datasetRecords) {
    $collectionPath = $item.collectionPath
    $collectionFile = Join-Path $collectionPath 'collection.json'

    if ((Test-Path $collectionFile) -and -not $Force) {
        continue
    }

    $collectionParent = "../catalog.json"
    $collectionRoot = "../../catalog.json"
    $codeToken = $item.code.ToLowerInvariant()

    $collection = [ordered]@{
        type = 'Collection'
        stac_version = '1.1.0'
        id = ($item.relativePath -replace '\\', '/')
        title = "$($item.code) - $($item.title)"
        description = "Geodato pubblicato su data.geo.ti.ch: $($item.title)."
        license = 'other'
        extent = [ordered]@{
            spatial = [ordered]@{ bbox = @(@(8.3, 45.8, 9.3, 46.7)) }
            temporal = [ordered]@{ interval = @(@($null, $null)) }
        }
        keywords = @($item.code, $item.title, $item.categoryFolder)
        links = @(
            [ordered]@{ rel = 'root'; href = $collectionRoot; type = 'application/json' },
            [ordered]@{ rel = 'parent'; href = $collectionParent; type = 'application/json' },
            [ordered]@{ rel = 'self'; href = './collection.json'; type = 'application/json' },
            [ordered]@{ rel = 'related'; href = $geoportaleUrl; type = 'text/html'; title = 'Geoportale Ticino' },
            [ordered]@{ rel = 'related'; href = $mapUrl; type = 'text/html'; title = 'Geoportale Ticino - Mappa' },
            [ordered]@{ rel = 'related'; href = $conditionsUrl; type = 'text/html'; title = 'Condizioni di utilizzo' },
            [ordered]@{ rel = 'via'; href = "https://data.geo.ti.ch/?p=$($item.page)"; type = 'text/html'; title = 'Scheda dataset su data.geo.ti.ch' }
        )
    }

    New-JsonFile -Path $collectionFile -Value $collection
}

$summary = [ordered]@{
    totalDatasets = $datasetRecords.Count
    categories = $categoryDefinitions.Keys
    generatedCollections = ($datasetRecords | Where-Object { -not (Test-Path (Join-Path $_.collectionPath 'collection.json')) }).Count
}

Write-Host "Generated/updated catalog with $($datasetRecords.Count) datasets."
Write-Host ($summary | ConvertTo-Json -Depth 5)