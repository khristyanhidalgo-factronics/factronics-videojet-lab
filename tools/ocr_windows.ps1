<#
OCR con Windows.Media.Ocr (WinRT) via PowerShell - sin instalar nada.
Uso: powershell -File tools/ocr_windows.ps1 -RutaImagen C:\...\pag_00.jpg [-Salida texto.txt]
Imprime (o guarda) el texto reconocido.
#>
param(
    [Parameter(Mandatory = $true)][string]$RutaImagen,
    [string]$Salida = ''
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.FileAccessMode, Windows.Foundation, ContentType = WindowsRuntime]

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

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
    $idioma = New-Object Windows.Globalization.Language 'en-US'
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($idioma)
}
if ($null -eq $engine) {
    Write-Error 'OCR no disponible en este sistema'
    exit 2
}
$resultado = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
if ($Salida -ne '') {
    $resultado.Text | Out-File -FilePath $Salida -Encoding UTF8 -NoNewline
} else {
    $resultado.Text
}
