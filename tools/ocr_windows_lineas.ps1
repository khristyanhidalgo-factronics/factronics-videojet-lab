<#
OCR con Windows.Media.Ocr (WinRT) y salida JSON con lineas y coordenadas.
Sin instalar nada: usa el motor OCR del sistema.

Uso:
  powershell -File tools/ocr_windows_lineas.ps1 -RutaImagen C:\...\pag.png [-Salida C:\...\pag.json] [-Idioma es-MX]

Salida: { ancho, alto, idioma, lineas: [ { texto, x, y, w, h, palabras:[...] } ] }
#>
param(
    [Parameter(Mandatory = $true)][string]$RutaImagen,
    [string]$Salida = '',
    [string]$Idioma = ''
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.FileAccessMode, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime]

$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await($tarea, $tipo) {
    $generico = $asTask.MakeGenericMethod($tipo)
    $net = $generico.Invoke($null, @($tarea))
    $net.Wait(-1) | Out-Null
    $net.Result
}

$archivo = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($RutaImagen)) ([Windows.Storage.StorageFile])
$stream = Await ($archivo.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$engine = $null
if ($Idioma -ne '') {
    $lang = New-Object Windows.Globalization.Language $Idioma
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
}
if ($null -eq $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}
if ($null -eq $engine) {
    Write-Error 'OCR no disponible en este sistema'
    exit 2
}

$resultado = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

$lineas = @()
foreach ($linea in $resultado.Lines) {
    if ($null -eq $linea -or $linea.Words.Count -eq 0) { continue }
    $palabras = @()
    $minX = [double]::MaxValue
    $minY = [double]::MaxValue
    $maxX = 0.0
    $maxY = 0.0
    foreach ($p in $linea.Words) {
        $r = $p.BoundingRect
        if ($r.X -lt $minX) { $minX = $r.X }
        if ($r.Y -lt $minY) { $minY = $r.Y }
        if (($r.X + $r.Width) -gt $maxX) { $maxX = $r.X + $r.Width }
        if (($r.Y + $r.Height) -gt $maxY) { $maxY = $r.Y + $r.Height }
        $palabras += [pscustomobject]@{
            t = $p.Text
            x = [math]::Round($r.X, 1)
            y = [math]::Round($r.Y, 1)
            w = [math]::Round($r.Width, 1)
            h = [math]::Round($r.Height, 1)
        }
    }
    $lineas += [pscustomobject]@{
        texto = $linea.Text
        x = [math]::Round($minX, 1)
        y = [math]::Round($minY, 1)
        w = [math]::Round($maxX - $minX, 1)
        h = [math]::Round($maxY - $minY, 1)
        palabras = $palabras
    }
}

$salidaObj = [pscustomobject]@{
    ancho = $bitmap.PixelWidth
    alto = $bitmap.PixelHeight
    idioma = $engine.RecognizerLanguage.LanguageTag
    lineas = $lineas
}
$json = $salidaObj | ConvertTo-Json -Depth 6 -Compress

if ($Salida -ne '') {
    [System.IO.File]::WriteAllText($Salida, $json, (New-Object System.Text.UTF8Encoding($false)))
} else {
    $json
}
