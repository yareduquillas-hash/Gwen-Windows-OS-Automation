$sw = [System.Diagnostics.Stopwatch]::StartNew()

try {
    Add-Type -AssemblyName System.Drawing
    Add-Type -AssemblyName System.Windows.Forms

    # Load WinRT Types
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Storage.Streams.RandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]

    $width = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
    $height = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height
    $cropW = [int]($width * 0.6)
    $cropH = [int]($height * 0.6)
    $left = [int]($width * 0.2)
    $top = [int]($height * 0.2)

    $bmp = New-Object System.Drawing.Bitmap($cropW, $cropH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $sz = New-Object System.Drawing.Size($cropW, $cropH)
    $g.CopyFromScreen($left, $top, 0, 0, $sz, [System.Drawing.CopyPixelOperation]::SourceCopy)

    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $ms.Position = 0

    $ras = [Windows.Storage.Streams.RandomAccessStream]::AsStreamForRead($ms).AsRandomAccessStream()
    $decoderTask = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($ras)
    while (-not $decoderTask.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $decoder = $decoderTask.GetResults()

    $bmpTask = $decoder.GetSoftwareBitmapAsync()
    while (-not $bmpTask.IsCompleted) { Start-Sleep -Milliseconds 5 }
    $softwareBitmap = $bmpTask.GetResults()

    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguage()
    if ($engine -ne $null) {
        $ocrTask = $engine.RecognizeAsync($softwareBitmap)
        while (-not $ocrTask.IsCompleted) { Start-Sleep -Milliseconds 5 }
        $result = $ocrTask.GetResults()
        $text = $result.Text
    } else {
        $text = "ENGINE_NULL"
    }

    $g.Dispose()
    $bmp.Dispose()
    $ms.Dispose()

    $sw.Stop()
    Write-Host "TEXT: $text"
    Write-Host "TIME: $($sw.ElapsedMilliseconds) ms"
} catch {
    Write-Host "ERROR: $_"
}
