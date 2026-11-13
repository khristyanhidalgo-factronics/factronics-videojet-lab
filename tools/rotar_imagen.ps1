# Rota una imagen PNG/JPG con System.Drawing (sin instalar nada).
# Uso: powershell -File tools/rotar_imagen.ps1 -RutaImagen x.png -Salida y.png -Grados 90
param(
    [Parameter(Mandatory = $true)][string]$RutaImagen,
    [Parameter(Mandatory = $true)][string]$Salida,
    [ValidateSet(90, 180, 270)][int]$Grados = 90
)

Add-Type -AssemblyName System.Drawing
$bmp = [System.Drawing.Bitmap]::FromFile($RutaImagen)
try {
    switch ($Grados) {
        90  { $bmp.RotateFlip([System.Drawing.RotateFlipType]::Rotate90FlipNone) }
        180 { $bmp.RotateFlip([System.Drawing.RotateFlipType]::Rotate180FlipNone) }
        270 { $bmp.RotateFlip([System.Drawing.RotateFlipType]::Rotate270FlipNone) }
    }
    $bmp.Save($Salida, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $bmp.Dispose()
}
Write-Output "OK $Salida ($Grados grados)"
