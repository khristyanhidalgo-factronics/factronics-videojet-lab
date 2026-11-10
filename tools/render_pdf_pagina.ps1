# Renderiza una pagina de PDF a PNG con Windows.Data.Pdf (WinRT, sin instalar nada).
# Uso: powershell -File tools/render_pdf_pagina.ps1 -RutaPdf C:\...\x.pdf -Pagina 29 -Salida C:\...\pag.png [-Ancho 2200]
param(
    [Parameter(Mandatory = $true)][string]$RutaPdf,
    [Parameter(Mandatory = $true)][int]$Pagina,
    [Parameter(Mandatory = $true)][string]$Salida,
    [int]$Ancho = 2200
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$null = [Windows.Data.Pdf.PdfDocument, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfPageRenderOptions, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.FileAccessMode, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Foundation, ContentType = WindowsRuntime]

$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
$asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
})[0]

function Await($tarea, $tipo) {
    $generico = $asTask.MakeGenericMethod($tipo)
    $net = $generico.Invoke($null, @($tarea))
    $net.Wait(-1) | Out-Null
    $net.Result
}

function AwaitAction($tarea) {
    $net = $asTaskAction.Invoke($null, @($tarea))
    $net.Wait(-1) | Out-Null
}

$archivoPdf = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($RutaPdf)) ([Windows.Storage.StorageFile])
$doc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($archivoPdf)) ([Windows.Data.Pdf.PdfDocument])
if ($Pagina -lt 1 -or $Pagina -gt $doc.PageCount) {
    Write-Error "Pagina fuera de rango (1..$($doc.PageCount))"
    exit 3
}
$pag = $doc.GetPage($Pagina - 1)
$opciones = New-Object Windows.Data.Pdf.PdfPageRenderOptions
$opciones.DestinationWidth = $Ancho

# Crear/reemplazar el archivo de salida
if (Test-Path $Salida) { Remove-Item $Salida -Force }
$carpeta = Await ([Windows.Storage.StorageFolder]::GetFolderFromPathAsync((Split-Path -Parent $Salida))) ([Windows.Storage.StorageFolder])
$nuevo = Await ($carpeta.CreateFileAsync((Split-Path -Leaf $Salida), [Windows.Storage.CreationCollisionOption]::ReplaceExisting)) ([Windows.Storage.StorageFile])
$stream = Await ($nuevo.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)) ([Windows.Storage.Streams.IRandomAccessStream])
AwaitAction ($pag.RenderToStreamAsync($stream, $opciones))
$stream.FlushAsync() | Out-Null
$stream.Dispose()
$pag.Dispose()
Write-Output "OK $Salida ($($doc.PageCount) paginas)"
